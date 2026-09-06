from fastapi.testclient import TestClient
from server.main import create_app


def make_client() -> TestClient:
    return TestClient(create_app())


def test_health():
    with make_client() as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["llm_ready"] is True          # mock 엔진 로드 확인
        assert body["llm_backend"] == "mock"


def test_analyze_e2e_stub():
    with make_client() as client:
        # 위험 표현이 없는 중립 질문으로 변경 (2단계에서 pre 룰이 활성화됨)
        r = client.post("/api/analyze", json={"query": "예금과 적금의 차이가 뭐야?"})
        assert r.status_code == 200
        body = r.json()
        assert "raw_response" in body and "final_response" in body
        assert "safety" in body and "evidence" in body
        assert body["safety"]["action"] == "pass" # 1단계: 검증 미연결


def test_analyze_validation_error():
    with make_client() as client:
        r = client.post("/api/analyze", json={"query": ""})
        assert r.status_code == 422               # Pydantic 입력 검증


def test_logs_endpoint_available():
    """로그 API 가용성 검증 (건수 검증은 test_logger.py 담당)."""
    with make_client() as client:
        r = client.get("/api/logs")
        assert r.status_code == 200
        body = r.json()
        assert "total" in body and "items" in body

