from server.core.llm.base import LLMEngine


class MockEngine(LLMEngine):
    """모델 파일 없이 파이프라인을 개발/테스트하기 위한 엔진.
    일부러 '위험한 답변'을 흉내 내서 이후 단계의 Validator가
    실제로 잡아내는지 검증하는 용도로도 사용한다.
    """

    def __init__(self) -> None:
        self._ready = False

    def load(self) -> None:
        self._ready = True

    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        return (
            "[MOCK] 요청하신 내용에 대한 임시 응답입니다. "
            "이 응답은 실제 모델이 아닌 개발용 목업입니다."
        )

    def is_ready(self) -> bool:
        return self._ready
