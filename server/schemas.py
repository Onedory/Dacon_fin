from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------- 공통 열거형 ----------

class Domain(str, Enum):
    banking = "banking"
    insurance = "insurance"
    investment = "investment"
    general = "general"
    auto = "auto"  # 요청 시 자동 판별


class RiskLevel(str, Enum):
    none = "none"
    low = "low"
    mid = "mid"
    high = "high"


class PolicyAction(str, Enum):
    pass_ = "pass"
    warn = "warn"
    mask = "mask"        # PII 부분 마스킹
    rewrite = "rewrite"
    block = "block"


# ---------- 파이프라인 내부 모델 ----------

class RuleViolation(BaseModel):
    rule_id: str
    description: str
    severity: RiskLevel
    matched_text: Optional[str] = None


class PolicyDecision(BaseModel):
    """PolicyLayer의 판정 결과. pre(질문)/post(응답) 공통 포맷.
    masked_text: mask 룰 위반 시 '마스킹 제안본'. 적용 여부는 orchestrator가 결정.
    """
    risk_level: RiskLevel = RiskLevel.none
    action: PolicyAction = PolicyAction.pass_
    violations: list[RuleViolation] = []
    masked_text: Optional[str] = None


class ClassificationResult(BaseModel):
    """분류기 출력. 구현 방식(keyword/ML/LLM)과 무관한 공통 계약."""
    domain: Domain
    confidence: float = 0.0
    matched_keywords: list[str] = []


class Evidence(BaseModel):
    doc_id: str
    title: str
    content: str = ""            # 원문 전체
    snippet: str = ""            # 표시용 요약
    score: float = 0.0
    metadata: dict = {}          # source, url, category 등


# ---------- API 계약 ----------

class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    domain: Domain = Domain.auto


class SafetyReport(BaseModel):
    risk_level: RiskLevel
    action: PolicyAction
    violated_rules: list[RuleViolation]


class AnalyzeResponse(BaseModel):
    domain: Domain
    raw_response: str
    safety: SafetyReport
    final_response: str
    evidence: list[Evidence]
    latency_ms: int


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str
    app_env: str
    llm_backend: str
    llm_ready: bool
    llm_error: Optional[str] = None
    model_load_seconds: Optional[float] = None   # cold start
    retriever_backend: str


class LogEntry(BaseModel):
    id: int
    ts: str
    user_query: str
    domain: str
    risk_level: str
    action: str
    final_response: str


class LogsResponse(BaseModel):
    total: int
    items: list[LogEntry]
