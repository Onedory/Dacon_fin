"""원본 문서 → 전처리/토큰화 → BM25 인덱스 생성 (재현 가능).
사용: python scripts/build_index.py
출력: data/index/{docs,spec}_bm25.pkl + *_meta.json (인덱스/메타 분리)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # ← server import보다 먼저!

import json
import pickle
import yaml
from rank_bm25 import BM25Okapi
from server.core.retriever.tokenizer import tokenize   # ← 이제 성공

INDEX_DIR = ROOT / "data" / "index"

def _build(corpus_texts: list[str], meta: list[dict], name: str) -> None:
    tokenized = [tokenize(t) for t in corpus_texts]
    bm25 = BM25Okapi(tokenized)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_DIR / f"{name}_bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)
    with open(INDEX_DIR / f"{name}_bm25_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"[build_index] {name}: {len(meta)} docs -> {INDEX_DIR}/{name}_bm25.pkl")


def build_docs_index() -> None:
    """Financial Document Retrieval 용 인덱스."""
    with open(ROOT / "data" / "docs" / "financial_docs.yaml", encoding="utf-8") as f:
        docs = yaml.safe_load(f)["documents"]
    texts = [f"{d['title']} {d['content']}" for d in docs]
    _build(texts, docs, "docs")


def build_spec_index() -> None:
    """Safety Spec Retrieval 용 인덱스 (룰 설명 텍스트 기반)."""
    with open(ROOT / "rules" / "safety_spec.yaml", encoding="utf-8") as f:
        rules = yaml.safe_load(f)["rules"]
    texts = [f"{r['category']} {r['description']}" for r in rules]
    meta = [{"doc_id": r["rule_id"], "title": r["description"],
             "content": r["description"], "source": "FinGuard Safety Spec",
             "category": r["category"]} for r in rules]
    _build(texts, meta, "spec")


if __name__ == "__main__":
    build_docs_index()
    build_spec_index()
