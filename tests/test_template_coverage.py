import yaml

SPEC = "rules/safety_spec.yaml"
TPL = "rules/rewrite_templates.yaml"


def _load():
    with open(SPEC, encoding="utf-8") as f:
        rules = yaml.safe_load(f)["rules"]
    with open(TPL, encoding="utf-8") as f:
        templates = {t["template_id"]: t for t in yaml.safe_load(f)["templates"]}
    return rules, templates


def test_every_rewrite_rule_has_template_id():
    rules, _ = _load()
    missing = [r["rule_id"] for r in rules
               if r["action"] == "rewrite" and not r.get("rewrite_template_id")]
    assert not missing, f"rewrite 룰에 template_id 누락: {missing}"


def test_every_referenced_template_exists():
    rules, templates = _load()
    broken = [(r["rule_id"], r["rewrite_template_id"]) for r in rules
              if r.get("rewrite_template_id")
              and r["rewrite_template_id"] not in templates]
    assert not broken, f"존재하지 않는 template_id 참조: {broken}"


def test_no_orphan_templates():
    rules, templates = _load()
    referenced = {r.get("rewrite_template_id") for r in rules}
    orphans = [tid for tid in templates if tid not in referenced]
    assert not orphans, f"어떤 룰에서도 참조되지 않는 템플릿: {orphans}"


def test_templates_have_required_fields():
    _, templates = _load()
    for tid, t in templates.items():
        assert t.get("safe_sentence"), f"{tid}: safe_sentence 누락"
        assert t.get("notice"), f"{tid}: notice 누락"
