import pytest
from server.core.policy.rule_engine import RuleEngine
from server.pipeline.rewriter import TemplateRewriter


@pytest.fixture(scope="module")
def setup():
    engine = RuleEngine("rules/safety_spec.yaml")
    engine.load_rules()
    rewriter = TemplateRewriter("rules/rewrite_templates.yaml",
                                engine.rewrite_template_map())
    rewriter.load()
    return engine, rewriter


def test_risky_sentence_replaced_safe_part_preserved(setup):
    engine, rewriter = setup
    raw = "이 상품은 원금이 보장됩니다. 가입은 앱에서 하실 수 있습니다."
    d = engine.evaluate(raw, "post", "general")
    out = rewriter.rewrite(raw, d.violations)
    assert "원금이 보장" not in out                    # 위험 표현 제거
    assert "가입은 앱에서 하실 수 있습니다." in out      # 정상 문장 보존 (조건 4)
    assert "원금 손실이 발생할 수 있습니다" in out       # 안전 대체 문장
    assert "※" in out                                  # 주의 문구 첨부


def test_rewrite_is_deterministic(setup):
    engine, rewriter = setup
    raw = "이 보험은 무조건 보장됩니다."
    d = engine.evaluate(raw, "post", "general")
    assert rewriter.rewrite(raw, d.violations) == rewriter.rewrite(raw, d.violations)


def test_multiple_violations_multiple_notices(setup):
    engine, rewriter = setup
    raw = "이 보험은 무조건 보장됩니다. 해지해도 손해 없습니다."
    d = engine.evaluate(raw, "post", "general")
    out = rewriter.rewrite(raw, d.violations)
    assert "무조건 보장" not in out and "손해 없" not in out
    assert out.count("※") >= 2                        # 템플릿별 notice 각각 첨부


def test_warn_only_violations_not_rewritten(setup):
    engine, rewriter = setup
    raw = "기존 보험 해지하고 갈아타세요."               # FIN-INS-007 = warn
    d = engine.evaluate(raw, "post", "general")
    out = rewriter.rewrite(raw, d.violations)
    assert out.startswith(raw.split(".")[0][:5]) or raw in out  # warn 룰은 본문 유지
