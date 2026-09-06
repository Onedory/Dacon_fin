from server.pipeline.prompt_builder import build_messages, SYSTEM_PROMPT
from server.schemas import Evidence

SPEC = [Evidence(doc_id="FIN-INV-001", title="확정수익 표현 금지")]
DOCS = [Evidence(doc_id="inv-001", title="투자 위험", content="원금 손실 가능")]


def test_structure_and_roles():
    msgs = build_messages("투자 질문", SPEC, DOCS)
    assert msgs[0]["role"] == "system" and msgs[0]["content"] == SYSTEM_PROMPT
    assert msgs[1]["role"] == "user"


def test_spec_and_evidence_included():
    user = build_messages("투자 질문", SPEC, DOCS)[1]["content"]
    assert "[적용 안전 규칙]" in user and "FIN-INV-001" in user
    assert "[참고 문서 inv-001]" in user and "원금 손실 가능" in user
    assert "[질문]\n투자 질문" in user


def test_empty_context_omits_blocks():
    user = build_messages("질문", [], [])[1]["content"]
    assert "[적용 안전 규칙]" not in user and "[참고 문서" not in user
