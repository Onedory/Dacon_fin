import json
import pickle
from pathlib import Path
from server.core.retriever.base import BaseRetriever
from server.core.retriever.tokenizer import tokenize
from server.schemas import Evidence

SNIPPET_LEN = 150


class BM25Retriever(BaseRetriever):
    """BM25 검색 구현체 (MVP).
    - index(.pkl)와 metadata(_meta.json)를 분리 저장/로드
    - 의미적 유사성(동의어 등)은 다루지 않음 → embedding/hybrid 교체 지점
    """

    def __init__(self, index_path: str):
        self._index_path = Path(index_path)
        self._meta_path = Path(str(index_path).replace(".pkl", "_meta.json"))
        self._bm25 = None
        self._meta: list[dict] = []

    def load_index(self) -> None:
        with open(self._index_path, "rb") as f:
            self._bm25 = pickle.load(f)
        with open(self._meta_path, encoding="utf-8") as f:
            self._meta = json.load(f)

    def search(self, query: str, top_k: int) -> list[Evidence]:
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for idx, score in ranked:
            if score <= 0:                    # 무관 문서 제외
                continue
            m = self._meta[idx]
            results.append(Evidence(
                doc_id=m["doc_id"], title=m["title"],
                content=m["content"],
                snippet=m["content"][:SNIPPET_LEN],
                score=round(float(score), 4),
                metadata={k: m[k] for k in ("source", "url", "category") if k in m},
            ))
        return results

    def is_ready(self) -> bool:
        return self._bm25 is not None
