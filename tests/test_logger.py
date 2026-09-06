from fastapi.testclient import TestClient
from server.main import create_app


def make_client():
    return TestClient(create_app())


def test_analyze_creates_log_entry():
    with make_client() as client:
        client.post("/api/analyze", json={"query": "예금과 적금의 차이가 뭐야?"})
        body = client.get("/api/logs").json()
        assert body["total"] >= 1
        assert body["items"][0]["user_query"] == "예금과 적금의 차이가 뭐야?"
        assert body["items"][0]["action"] == "pass"


def test_pii_not_stored_in_log():
    with make_client() as client:
        client.post("/api/analyze",
                    json={"query": "900101-1234567 인데 적금 상품 알려줘"})
        text = client.get("/api/logs?limit=100").text
        assert "900101-1234567" not in text          # 로그 응답 전체에 원문 부재
        assert "[MASKED]" in text                     # 마스킹본이 저장됨


def test_blocked_request_also_logged():
    with make_client() as client:
        client.post("/api/analyze", json={"query": "내 계좌 잔액 조회해줘"})
        items = client.get("/api/logs").json()["items"]
        assert items[0]["action"] == "block"
