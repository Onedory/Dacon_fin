from abc import ABC, abstractmethod
from server.schemas import ClassificationResult


class BaseClassifier(ABC):
    """도메인 분류기 인터페이스.
    Orchestrator는 이 인터페이스에만 의존한다.
    향후 ML/LLM 분류기는 이 클래스를 구현하고 factory에 등록만 하면 된다.
    """

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def classify(self, text: str) -> ClassificationResult:
        """반드시 auto가 아닌 확정 도메인을 반환. 판단 불가 시 general."""
