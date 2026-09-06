import os
import pytest
from pathlib import Path

MODEL = os.getenv("MODEL_PATH", "./models/qwen2.5-0.5b-instruct-q4_k_m.gguf")
pytestmark = pytest.mark.skipif(not Path(MODEL).exists(),
                                reason="GGUF 모델 파일 없음 (CI/미다운로드 환경)")


@pytest.fixture(scope="module")
def engine():
    from server.core.llm.llama_cpp_engine import LlamaCppEngine
    e = LlamaCppEngine(MODEL, n_ctx=2048, n_threads=2)
    e.load()
    assert e.is_ready(), e.load_error()
    return e


def test_cold_start_recorded(engine):
    assert engine.load_seconds() and engine.load_seconds() > 0


def test_chat_template_korean_response(engine):
    out = engine.chat(
        [{"role": "system", "content": "한 문장으로 답하세요."},
         {"role": "user", "content": "적금이 무엇인지 설명해줘"}],
        max_tokens=100, temperature=0.3)
    assert isinstance(out, str) and len(out) > 5


def test_missing_model_graceful():
    from server.core.llm.llama_cpp_engine import LlamaCppEngine
    e = LlamaCppEngine("./models/not_exist.gguf", 2048, 2)
    e.load()                                  # 예외 미발생
    assert not e.is_ready() and "모델 파일 없음" in e.load_error()
