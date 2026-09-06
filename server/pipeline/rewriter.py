import re
import yaml
from server.schemas import RuleViolation

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

_FALLBACK = {
    "safe_sentence": ("해당 내용은 단정적으로 안내드리기 어렵습니다. "
                      "정확한 내용은 공식 상담 채널에서 확인해 주세요."),
    "notice": "※ 금융상품의 조건은 약관과 시장 상황에 따라 달라질 수 있습니다.",
}


class TemplateRewriter:
    """결정론적 템플릿 재작성기.
    - LLM 미사용: 동일 입력 → 동일 출력 보장
    - 위반 표현이 포함된 '문장'만 안전 문장으로 교체하고, 나머지 원문은 보존
    - 템플릿의 notice(주의 문구)를 말미에 중복 없이 첨부
    """

    def __init__(self, templates_path: str, rule_template_map: dict[str, str]):
        self._path = templates_path
        self._map = rule_template_map          # rule_id → template_id (RuleEngine 제공)
        self._templates: dict[str, dict] = {}

    def load(self) -> None:
        with open(self._path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        self._templates = {t["template_id"]: t for t in raw["templates"]}

    def rewrite(self, text: str, violations: list[RuleViolation]) -> str:
        sentences = [s for s in _SENT_SPLIT.split(text) if s.strip()] or [text]
        notices: list[str] = []

        for v in violations:
            tid = self._map.get(v.rule_id)
            if tid is None:            # rewrite 대상 룰이 아님 (warn/mask/block)
                continue
            tpl = self._templates.get(tid, _FALLBACK)

            replaced = False
            for i, s in enumerate(sentences):
                if v.matched_text and v.matched_text in s:
                    sentences[i] = tpl["safe_sentence"]
                    replaced = True
            if not replaced:           # 문장 매칭 실패 시 안전 문장 첨부 (방어)
                sentences.append(tpl["safe_sentence"])
            if tpl["notice"] not in notices:
                notices.append(tpl["notice"])

        deduped: list[str] = []        # 동일 안전 문장 연속 중복 제거
        for s in sentences:
            if not deduped or deduped[-1] != s:
                deduped.append(s)

        body = " ".join(deduped)
        return body + ("\n" + "\n".join(notices) if notices else "")
