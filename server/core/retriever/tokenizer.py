from kiwipiepy import Kiwi

# 검색 유효 품사: 명사류, 동사/형용사 어근, 외국어, 숫자
_VALID_TAGS = ("NNG", "NNP", "NNB", "VV", "VA", "SL", "SN", "XR")

_kiwi = Kiwi()


def tokenize(text: str) -> list[str]:
    """인덱스 빌드와 검색 질의에 동일하게 사용해야 한다 (일관성 필수)."""
    return [t.form for t in _kiwi.tokenize(text) if t.tag.startswith(_VALID_TAGS)]
