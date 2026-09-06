from server.core.retriever.base import BaseRetriever
from server.schemas import Evidence


class NullRetriever(BaseRetriever):
    """1단계 스텁. 인덱스가 없어도 파이프라인이 E2E로 돌게 한다."""

    def load_index(self) -> None:
        pass

    def search(self, query: str, top_k: int) -> list[Evidence]:
        return []

    def is_ready(self) -> bool:
        return True
