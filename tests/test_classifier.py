import yaml
import pytest
from server.core.classifier.keyword_classifier import KeywordClassifier
from server.schemas import Domain


@pytest.fixture(scope="module")
def clf():
    c = KeywordClassifier("rules/domain_keywords.yaml")
    c.load()
    return c


def test_unknown_falls_back_to_general(clf):
    r = clf.classify("오늘 날씨 어때?")
    assert r.domain == Domain.general and r.confidence == 0.0


def test_ambiguous_tie_falls_back_to_general(clf):
    r = clf.classify("물가가 오르면 예금이 유리해, 투자가 유리해?")  # 2:2 동점
    assert r.domain == Domain.general


def test_result_structure(clf):
    r = clf.classify("실비보험 청구 방법 알려줘")
    assert r.domain == Domain.insurance
    assert 0.0 < r.confidence <= 1.0
    assert "보험" in r.matched_keywords


def test_testset_40_accuracy(clf):
    with open("tests/data/testset_40.yaml", encoding="utf-8") as f:
        items = yaml.safe_load(f)["items"]
    assert len(items) == 40

    misses = []
    for it in items:
        r = clf.classify(it["query"])
        if r.domain.value != it["expected_domain"]:
            misses.append(f"{it['id']} '{it['query']}' "
                          f"expected={it['expected_domain']} got={r.domain.value}")

    accuracy = 1 - len(misses) / len(items)
    # 오분류 사례 확인용 출력 (pytest -s 로 확인)
    print(f"\n[classification] accuracy={accuracy:.1%} misses={len(misses)}")
    for m in misses:
        print("  MISS:", m)
    assert accuracy >= 0.9, f"accuracy {accuracy:.1%} < 90%\n" + "\n".join(misses)
