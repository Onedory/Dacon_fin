from abc import ABC, abstractmethod
from typing import Optional


class LLMEngine(ABC):
    """LLM 추상 인터페이스. 구현체 교체는 factory + 설정으로만."""

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str: ...

    @abstractmethod
    def is_ready(self) -> bool: ...

    # --- 5단계 확장 (기본 구현 제공 → 기존 mock 엔진 무수정 호환) ---

    def chat(self, messages: list[dict], max_tokens: int, temperature: float) -> str:
        """role별 메시지 기반 생성. 기본 구현은 텍스트 연결 후 generate 위임."""
        joined = "\n\n".join(f"[{m['role']}]\n{m['content']}" for m in messages)
        return self.generate(joined, max_tokens, temperature)

    def load_error(self) -> Optional[str]:
        """로드 실패 사유 (health 노출용). 정상이면 None."""
        return None

    def load_seconds(self) -> Optional[float]:
        """cold start(모델 로드) 소요 시간."""
        return None
