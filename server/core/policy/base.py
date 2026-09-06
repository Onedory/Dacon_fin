from abc import ABC, abstractmethod
from typing import Literal
from server.schemas import PolicyDecision


class PolicyLayer(ABC):
    """Financial Safety Specification 적용 계층.

    설계 원칙:
    - 답변을 '생성'하지 않는다. 텍스트를 '판정'만 한다.
    - 동일 인터페이스로 두 시점에 호출된다:
        stage="pre"  : 사용자 질문 검사 (PII, 금지 요청 등)
        stage="post" : LLM 응답 검증 (Safety Validation)
    - 판정 결과(PolicyDecision)에 따라 orchestrator가 후속 조치를 결정한다.
    2단계에서 rule_engine.py(YAML 룰 기반)가 이 인터페이스를 구현한다.
    """

    @abstractmethod
    def load_rules(self) -> None:
        ...

    @abstractmethod
    def evaluate(self, text: str, stage: Literal["pre", "post"],
                 domain: str) -> PolicyDecision:
        ...

    @abstractmethod
    def rule_count(self) -> int:
        ...
