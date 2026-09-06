import yaml
from server.core.classifier.base import BaseClassifier
from server.schemas import ClassificationResult, Domain

STRONG_WEIGHT = 2
WEAK_WEIGHT = 1


class KeywordClassifier(BaseClassifier):
    """키워드 테이블 기반 분류기 (MVP).
    - 점수 0 또는 1·2위 동점이면 general (과잉 분류보다 보수적 처리 우선)
    - confidence = top / (top + second) : 근소한 우세일수록 낮음
    """

    def __init__(self, keywords_path: str):
        self._path = keywords_path
        self._table: dict[str, list[tuple[str, int]]] = {}

    def load(self) -> None:
        with open(self._path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        for domain, groups in raw["domains"].items():
            entries = [(kw, STRONG_WEIGHT) for kw in groups.get("strong", [])]
            entries += [(kw, WEAK_WEIGHT) for kw in groups.get("weak", [])]
            self._table[domain] = entries

    def classify(self, text: str) -> ClassificationResult:
        scores: dict[str, int] = {}
        matched: dict[str, list[str]] = {}
        for domain, entries in self._table.items():
            hits = [kw for kw, _ in entries if kw in text]
            scores[domain] = sum(w for kw, w in entries if kw in text)
            matched[domain] = hits

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_domain, top = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0

        if top == 0 or top == second:   # 판단 불가/모호 → general
            return ClassificationResult(domain=Domain.general)

        return ClassificationResult(
            domain=Domain(top_domain),
            confidence=round(top / (top + second), 3),
            matched_keywords=matched[top_domain],
        )
