import threading
import time
from pathlib import Path
from typing import Optional
from server.core.llm.base import LLMEngine


class LlamaCppEngine(LLMEngine):
    """GGUF CPU 추론 엔진.
    - 모델 교체: MODEL_PATH 변경만으로 가능 (SFT GGUF 포함)
    - chat template: GGUF 내장 템플릿을 llama.cpp가 적용 (Qwen 공식 형식 준수)
    - 로드 실패 시 예외를 삼키고 상태로 보존 → 서버는 계속 기동
    """

    def __init__(self, model_path: str, n_ctx: int, n_threads: int,
                 max_concurrency: int = 1):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self._sem = threading.Semaphore(max_concurrency)
        self._llm = None
        self._error: Optional[str] = None
        self._load_seconds: Optional[float] = None

    def load(self) -> None:
        t0 = time.monotonic()
        try:
            if not Path(self.model_path).exists():
                raise FileNotFoundError(f"모델 파일 없음: {self.model_path}")
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False,
            )
            self._load_seconds = round(time.monotonic() - t0, 2)
        except MemoryError:
            self._error = "메모리 부족으로 모델 로드 실패 (스왑 설정 또는 더 작은 모델 필요)"
        except Exception as e:
            self._error = f"{type(e).__name__}: {e}"

    def chat(self, messages: list[dict], max_tokens: int, temperature: float) -> str:
        if not self.is_ready():
            raise RuntimeError(f"LLM not ready: {self._error}")
        with self._sem:                       # EC2 저사양 보호: 순차 처리
            out = self._llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        return out["choices"][0]["message"]["content"].strip()

    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        return self.chat([{"role": "user", "content": prompt}],
                         max_tokens, temperature)

    def is_ready(self) -> bool:
        return self._llm is not None

    def load_error(self) -> Optional[str]:
        return self._error

    def load_seconds(self) -> Optional[float]:
        return self._load_seconds
