import time
# import 추가
from server.pipeline.prompt_builder import build_messages
from server.config import Settings
from server.core.classifier.base import BaseClassifier
from server.core.llm.base import LLMEngine
from server.core.policy.base import PolicyLayer
from server.core.retriever.base import BaseRetriever
from server.pipeline.rewriter import TemplateRewriter
from server.schemas import (
    AnalyzeRequest, AnalyzeResponse, Domain, PolicyAction,
    PolicyDecision, RiskLevel, SafetyReport,
)

MSG_BLOCKED = ("요청하신 내용은 금융소비자 보호 정책에 따라 답변드릴 수 없습니다. "
               "정확한 확인이 필요한 경우 공식 채널을 이용해 주세요.")

_ACTION_ORDER = {
    PolicyAction.pass_: 0, PolicyAction.warn: 1, PolicyAction.mask: 2,
    PolicyAction.rewrite: 3, PolicyAction.block: 4,
}
_SEV_ORDER = {RiskLevel.none: 0, RiskLevel.low: 1, RiskLevel.mid: 2, RiskLevel.high: 3}


class Orchestrator:
    """파이프라인 제어자. PolicyLayer는 '판정'만 하고, 조치는 여기서 수행한다."""

    def __init__(self, settings: Settings, llm: LLMEngine,
                 spec_retriever: BaseRetriever, doc_retriever: BaseRetriever,
                 policy: PolicyLayer, classifier: BaseClassifier,
                 rewriter: TemplateRewriter, audit_logger=None):
        self.settings = settings
        self.llm = llm
        self.spec_retriever = spec_retriever
        self.doc_retriever = doc_retriever
        self.policy = policy
        self.classifier = classifier
        self.rewriter = rewriter
        self.audit_logger = audit_logger


    def run(self, req: AnalyzeRequest) -> AnalyzeResponse:
        t0 = time.monotonic()

        # ---- [분류] 도메인 결정 ----
        if req.domain == Domain.auto:
            domain = self.classifier.classify(req.query).domain
        else:
            domain = req.domain

        # ---- [PRE] 질문 검사 ----
        pre = self.policy.evaluate(req.query, "pre", domain.value)

        if pre.action == PolicyAction.block:
            return self._respond(domain, raw="", final=MSG_BLOCKED,
                                 decisions=[pre], evidence=[], t0=t0,
                                 user_query_safe=pre.masked_text or req.query)
        # mask: 마스킹 제안본 적용 (조치 주체 = orchestrator)
        query_for_llm = pre.masked_text if pre.masked_text else req.query

        # ---- [Spec Retrieval] 질문 관련 안전 규칙 검색 (LLM 프롬프트 컨텍스트용) ----
        spec_context = self.spec_retriever.search(query_for_llm, self.settings.retriever_top_k)

        # ---- [Doc Retrieval] 금융 문서 근거 검색 ----
        evidence = self.doc_retriever.search(query_for_llm, self.settings.retriever_top_k)

        # ---- 생성 (요청당 유일한 LLM 호출) ----
        messages = build_messages(query_for_llm, spec_context, evidence)
        raw = self.llm.chat(
            messages=messages,
            max_tokens=self.settings.llm_max_tokens,
            temperature=self.settings.llm_temperature,
        )

        # ---- [POST] 응답 검증 (Safety Validation) ----
        post = self.policy.evaluate(raw, "post", domain.value)

        final = raw
        if post.action == PolicyAction.block:
            final = MSG_BLOCKED
        elif post.action == PolicyAction.rewrite:
            final = self.rewriter.rewrite(raw, post.violations)
        elif post.action == PolicyAction.mask and post.masked_text:
            final = post.masked_text

        return self._respond(domain, raw=raw, final=final,
                             decisions=[pre, post], evidence=evidence, t0=t0,
                             user_query_safe=query_for_llm)
    # ---------- 내부 ----------

    def _respond(self, domain, raw, final, decisions, evidence, t0,
                 user_query_safe: str = ""):
        report = self._merge(decisions)
        latency = int((time.monotonic() - t0) * 1000)
        if self.audit_logger:
            self.audit_logger.log(
                user_query=user_query_safe, domain=domain.value,
                risk_level=report.risk_level.value, action=report.action.value,
                rule_ids=[v.rule_id for v in report.violated_rules],
                doc_ids=[e.doc_id for e in evidence],
                raw_response=raw, final_response=final, latency_ms=latency)
        return AnalyzeResponse(domain=domain, raw_response=raw, safety=report,
                               final_response=final, evidence=evidence,
                               latency_ms=latency)

    @staticmethod
    def _merge(decisions: list[PolicyDecision]) -> SafetyReport:
        violations = [v for d in decisions for v in d.violations]
        risk = max((d.risk_level for d in decisions), key=lambda s: _SEV_ORDER[s])
        action = max((d.action for d in decisions), key=lambda a: _ACTION_ORDER[a])
        return SafetyReport(risk_level=risk, action=action, violated_rules=violations)
