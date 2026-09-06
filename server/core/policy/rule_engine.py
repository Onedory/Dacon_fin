import re
import yaml
from typing import Literal, Optional
from server.core.policy.base import PolicyLayer
from server.schemas import PolicyAction, PolicyDecision, RiskLevel, RuleViolation

MASK_TOKEN = "[MASKED]"
REDACTED_FMT = "[REDACTED:{rule_id}]"

_SEVERITY_ORDER = {RiskLevel.none: 0, RiskLevel.low: 1, RiskLevel.mid: 2, RiskLevel.high: 3}
_ACTION_ORDER = {
    PolicyAction.pass_: 0, PolicyAction.warn: 1, PolicyAction.mask: 2,
    PolicyAction.rewrite: 3, PolicyAction.block: 4,
}


class _Rule:
    def __init__(self, raw: dict):
        self.rule_id: str = raw["rule_id"]
        self.category: str = raw["category"]
        self.description: str = raw["description"]
        self.severity = RiskLevel(raw["severity"])
        self.stage: str = raw["stage"]                    # pre | post | both
        self.domain: str = raw.get("domain", "any")
        self.action = PolicyAction(raw["action"])
        self.rewrite_template_id: Optional[str] = raw.get("rewrite_template_id")
        self.verification: str = raw.get("verification", "surface")
        self.spec_source: str = raw.get("spec_source", "")

        det = raw["detection"]
        self.detection_type: str = det["type"]            # regex | keyword | required_keyword_missing
        self.compiled: list[re.Pattern] = []
        self.keywords: list[str] = []
        self.required_any: list[str] = []
        if self.detection_type == "regex":
            self.compiled = [re.compile(p) for p in det["patterns"]]
        elif self.detection_type == "keyword":
            self.keywords = det["patterns"]
        elif self.detection_type == "required_keyword_missing":
            self.required_any = det["required_any"]
        else:
            raise ValueError(f"Unknown detection type: {self.detection_type}")

    @property
    def is_pii(self) -> bool:
        return self.category == "pii"


class RuleEngine(PolicyLayer):
    """Financial Safety Specification 판정 엔진.

    책임 범위:
    - 텍스트를 판정하고 PolicyDecision을 반환한다. (조치는 orchestrator 담당)
    - mask 룰의 경우 '마스킹 제안본(masked_text)'까지만 계산한다.
    - PII 룰 위반의 matched_text는 원문 대신 REDACTED 토큰으로 기록한다.
    - LLM/Retriever에 대한 어떤 의존성도 갖지 않는다.
    """

    def __init__(self, rules_path: str):
        self._rules_path = rules_path
        self._rules: list[_Rule] = []

    def load_rules(self) -> None:
        with open(self._rules_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        self._rules = [_Rule(r) for r in raw["rules"]]

    def rule_count(self) -> int:
        return len(self._rules)

    def list_rules(self) -> list[dict]:
        """/api/rules 용 요약. 패턴 원문은 포함하되 PII 원문과 무관하므로 안전."""
        return [
            {
                "rule_id": r.rule_id, "category": r.category,
                "description": r.description, "severity": r.severity.value,
                "stage": r.stage, "action": r.action.value,
                "verification": r.verification, "spec_source": r.spec_source,
            }
            for r in self._rules
        ]

    def evaluate(self, text: str, stage: Literal["pre", "post"],
                 domain: str = "general") -> PolicyDecision:
        violations: list[RuleViolation] = []
        masked = text
        mask_applied = False

        for rule in self._rules:
            if rule.stage not in (stage, "both"):
                continue
            if rule.domain != "any" and rule.domain != domain:
                continue

            if rule.detection_type == "regex":
                for pat in rule.compiled:
                    m = pat.search(masked if rule.is_pii else text)
                    if m:
                        violations.append(self._to_violation(rule, m.group(0)))
                        if rule.action == PolicyAction.mask:
                            masked = pat.sub(MASK_TOKEN, masked)
                            mask_applied = True
                        break  # 룰당 1회 기록

            elif rule.detection_type == "keyword":
                for kw in rule.keywords:
                    if kw in text:
                        violations.append(self._to_violation(rule, kw))
                        break

            elif rule.detection_type == "required_keyword_missing":
                # 주의: '고지 표현 부재' 감지일 뿐 위험 확정이 아니다.
                # 정밀 검증은 이후 RAG + Safety Judge(FIN-HAL-1xx) 담당.
                if text.strip() and not any(kw in text for kw in rule.required_any):
                    violations.append(self._to_violation(rule, None))

        return PolicyDecision(
            risk_level=self._max_severity(violations),
            action=self._max_action(violations),
            violations=violations,
            masked_text=masked if mask_applied else None,
        )

    # ---------- 내부 ----------

    def _to_violation(self, rule: _Rule, matched: Optional[str]) -> RuleViolation:
        # PII 원문이 로그/응답 payload에 남지 않도록 REDACTED 처리
        if rule.is_pii:
            matched = REDACTED_FMT.format(rule_id=rule.rule_id)
        return RuleViolation(
            rule_id=rule.rule_id, description=rule.description,
            severity=rule.severity, matched_text=matched,
        )

    @staticmethod
    def _max_severity(violations: list[RuleViolation]) -> RiskLevel:
        if not violations:
            return RiskLevel.none
        return max((v.severity for v in violations), key=lambda s: _SEVERITY_ORDER[s])

    def _max_action(self, violations: list[RuleViolation]) -> PolicyAction:
        if not violations:
            return PolicyAction.pass_
        rule_map = {r.rule_id: r.action for r in self._rules}
        actions = [rule_map[v.rule_id] for v in violations]
        return max(actions, key=lambda a: _ACTION_ORDER[a])
    def rewrite_template_map(self) -> dict[str, str]:
        """rule_id → rewrite_template_id (rewrite 룰만). Rewriter 주입용."""
        return {r.rule_id: r.rewrite_template_id
                for r in self._rules if r.rewrite_template_id}
