import pytest
from server.core.retriever.bm25_retriever import BM25Retriever

# 대표 질문 10개 → 기대 문서 (top-3 내 포함 목표)
CASES = [
    ("예금과 적금의 차이가 뭐야?", "bank-001"),
    ("예금자보호 한도는 얼마까지야?", "bank-002"),
    ("신용대출 금리는 어떻게 정해져?", "bank-003"),
    ("금융사기 문자를 받았는데 어떻게 해야 해?", "bank-004"),
    ("암보험 면책기간이 뭐야?", "ins-001"),
    ("보험금 청구 방법 알려줘", "ins-002"),
    ("보험 해지환급금은 어떻게 계산돼?", "ins-003"),
    ("보험 가입할 때 병력을 알려야 해?", "ins-004"),
    ("ETF와 펀드의 차이가 뭐야?", "inv-002"),
    ("주식 배당금은 언제 들어와?", "inv-004"),
]


@pytest.fixture(scope="module")
def retriever():
    r = BM25Retriever("data/index/docs_bm25.pkl")
    r.load_index()
    return r


def test_result_structure(retriever):
    results = retriever.search("보험금 청구 절차", top_k=3)
    assert results, "검색 결과 없음"
    e = results[0]
    assert e.doc_id and e.title and e.content and e.score > 0
    assert "source" in e.metadata and "url" in e.metadata


def test_irrelevant_query_returns_empty_or_low(retriever):
    results = retriever.search("오늘 저녁 메뉴 추천", top_k=3)
    assert all(r.score > 0 for r in results)   # 0점 문서 미포함 확인


def test_top3_inclusion(retriever):
    misses = []
    for query, expected in CASES:
        top3 = [e.doc_id for e in retriever.search(query, top_k=3)]
        if expected not in top3:
            misses.append(f"'{query}' expected={expected} got={top3}")
    rate = 1 - len(misses) / len(CASES)
    print(f"\n[retrieval] top-3 inclusion={rate:.0%} ({len(CASES)-len(misses)}/{len(CASES)})")
    for m in misses:
        print("  MISS:", m)
    assert rate >= 0.8, "\n".join(misses)


def test_spec_index_search():
    r = BM25Retriever("data/index/spec_bm25.pkl")
    r.load_index()
    results = r.search("원금 보장 수익", top_k=3)
    assert any(e.doc_id.startswith("FIN-INV") for e in results)
