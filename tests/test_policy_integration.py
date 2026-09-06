from fastapi.testclient import TestClient
from server.main import create_app
from server.core.llm.base import LLMEngine


class DangerousMockEngine(LLMEngine):
    """post 검증 테스트용: 일부러 위험한 응답을 생성하는 엔진."""
    def load(self): self._ready = True
    def is_ready(self): return True
    def generate(self, prompt, max_tokens, temperature):
        return "이 보험은 무조건 보장되고, 해지해도 손해 없습니다."


def make_client():
    return TestClient(create_app())


def test_pre_block_skips_llm():
    with make_client() as client:
        r = client.post("/api/analyze", json={"query": "내 계좌 잔액 조회해줘"})
        body = r.json()
        assert body["safety"]["action"] == "block"
        assert body["raw_response"] == ""              # LLM 미호출 확인
        assert "답변드릴 수 없습니다" in body["final_response"]


def test_pre_pii_masked_in_payload():
    with make_client() as client:
        r = client.post("/api/analyze",
                        json={"query": "900101-1234567 인데 적금 상품이 궁금해요"})
        text = r.text
        assert "900101-1234567" not in text            # 조건 3: 응답 전체에 원문 부재
        assert r.json()["safety"]["risk_level"] == "high"


def test_post_rewrite_on_dangerous_output():
    with make_client() as client:
        app = client.app
        app.state.orchestrator.llm = DangerousMockEngine()  # 위험 응답 엔진 주입
        r = client.post("/api/analyze", json={"query": "이 보험 어때요?"})
        body = r.json()
        ids = {v["rule_id"] for v in body["safety"]["violated_rules"]}
        assert "FIN-INS-001" in ids and "FIN-INS-004" in ids
        assert body["safety"]["action"] == "rewrite"
        assert body["final_response"] != body["raw_response"]  # 재작성 확인


def test_rules_endpoint():
    with make_client() as client:
        r = client.get("/api/rules")
        body = r.json()
        assert body["count"] == 26
        assert all("spec_source" in rule for rule in body["rules"])
