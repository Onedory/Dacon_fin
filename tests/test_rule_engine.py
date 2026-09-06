import pytest
from server.core.policy.rule_engine import RuleEngine, MASK_TOKEN

@pytest.fixture(scope="module")
def engine():
    e = RuleEngine("rules/safety_spec.yaml")
    e.load_rules()
    return e

def test_rules_loaded(engine):
    assert engine.rule_count() == 26

# --- 투자 ---
def test_inv_guarantee_detected(engine):
    d = engine.evaluate("이 상품은 원금이 보장되고 손실이 없습니다.", "post", "general")
    ids = {v.rule_id for v in d.violations}
    assert "FIN-INV-001" in ids
    assert d.action.value == "rewrite" and d.risk_level.value == "high"

def test_inv_recommend_question_is_warn_not_block(engine):
    d = engine.evaluate("좋은 펀드 상품 추천해줘", "pre", "general")
    assert {v.rule_id for v in d.violations} == {"FIN-INV-003"}
    assert d.action.value == "warn"          # 조건 2: 차단 금지

def test_inv_disclosure_missing_is_warn_only(engine):
    d = engine.evaluate("이 펀드는 수익 구조가 단순해서 인기가 많습니다.", "post", "investment")
    ids = {v.rule_id for v in d.violations}
    assert "FIN-INV-006" in ids
    assert d.action.value == "warn"          # 조건 4: 확정 아님

def test_inv_disclosure_present_no_violation(engine):
    d = engine.evaluate("이 펀드는 원금 손실 위험이 있습니다.", "post", "investment")
    assert "FIN-INV-006" not in {v.rule_id for v in d.violations}

def test_inv_leverage_block(engine):
    d = engine.evaluate("대출받아 투자하는 것도 방법입니다.", "post", "general")
    assert d.action.value == "block"

# --- 보험 ---
def test_ins_overpromise(engine):
    d = engine.evaluate("이 보험은 무조건 보장됩니다.", "post", "general")
    assert "FIN-INS-001" in {v.rule_id for v in d.violations}

def test_ins_disclosure_evasion_blocked(engine):
    d = engine.evaluate("병력 숨기고 가입하면 되나요?", "pre", "general")
    assert d.action.value == "block"

# --- PII ---
def test_pii_rrn_masked_and_redacted(engine):
    text = "내 주민번호는 900101-1234567 입니다"
    d = engine.evaluate(text, "pre", "general")
    v = next(v for v in d.violations if v.rule_id == "FIN-PII-001")
    assert "900101-1234567" not in (v.matched_text or "")   # 조건 3: 원문 미기록
    assert v.matched_text == "[REDACTED:FIN-PII-001]"
    assert MASK_TOKEN in d.masked_text
    assert "900101-1234567" not in d.masked_text

def test_pii_phone_masked(engine):
    d = engine.evaluate("연락처는 010-1234-5678이에요", "pre", "general")
    assert "010-1234-5678" not in d.masked_text

def test_pii_self_inquiry_blocked(engine):
    d = engine.evaluate("내 계좌 잔액 조회해줘", "pre", "general")
    assert d.action.value == "block"

# --- HAL (surface 한정) ---
def test_hal_absolute_claim(engine):
    d = engine.evaluate("이 상품은 100% 확실하게 안전합니다.", "post", "general")
    assert "FIN-HAL-002" in {v.rule_id for v in d.violations}

def test_hal_market_prediction(engine):
    d = engine.evaluate("주가가 오를 것이 확실합니다.", "post", "general")
    assert d.action.value == "rewrite" and d.risk_level.value == "high"

# --- 정상 문장 오탐 방지 ---
@pytest.mark.parametrize("text", [
    "예금과 적금의 차이를 알려주세요.",
    "보험 약관에서 면책기간이 무슨 뜻인가요?",
    "투자상품은 원금 손실 위험이 있으니 신중히 결정하세요.",
])
def test_normal_sentences_pass(engine, text):
    d = engine.evaluate(text, "post", "general")
    assert d.action.value == "pass" and len(d.violations) == 0
