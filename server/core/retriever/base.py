from abc import ABC, abstractmethod
from server.schemas import Evidence


class BaseRetriever(ABC):
    """검색 추상 인터페이스.
    MVP: BM25 / 확장: embedding, hybrid — 구현체 추가 후 factory에 등록만 하면 됨.
    spec 검색과 문서 검색 모두 이 인터페이스를 공유한다(인덱스만 다름).
    """

    @abstractmethod
    def load_index(self) -> None:
        """직렬화된 인덱스 로드. 서버 기동 시 1회."""

    @abstractmethod
    def search(self, query: str, top_k: int) -> list[Evidence]:
        """질의 → 상위 k개 근거."""

    @abstractmethod
    def is_ready(self) -> bool:
        ...
