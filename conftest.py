"""pytest 공통 설정: mock 백엔드 + 테스트 전용 DB (.env와 무관)."""
import os
import pytest
from pathlib import Path

os.environ["LLM_BACKEND"] = "mock"
os.environ["DB_PATH"] = "./data/test_finguard.db"

from server.config import get_settings
get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def ensure_indexes():
    if not Path("data/index/docs_bm25.pkl").exists():
        from scripts.build_index import build_docs_index, build_spec_index
        build_docs_index()
        build_spec_index()
    yield
    Path("./data/test_finguard.db").unlink(missing_ok=True)   # 테스트 DB 정리
