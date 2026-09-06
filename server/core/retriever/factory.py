from server.config import Settings
from server.core.retriever.base import BaseRetriever
from server.core.retriever.null_retriever import NullRetriever
from server.core.retriever.bm25_retriever import BM25Retriever


def create_retriever(settings: Settings, index_path: str) -> BaseRetriever:
    if settings.retriever_backend == "null":
        return NullRetriever()
    if settings.retriever_backend == "bm25":
        return BM25Retriever(index_path)
    # 향후: "embedding", "hybrid" 등록 지점
    raise ValueError(f"Unknown RETRIEVER_BACKEND: {settings.retriever_backend}")
