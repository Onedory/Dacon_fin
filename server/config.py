from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """모든 교체 가능 요소의 단일 설정 지점.
    모델/리트리버 교체 시 코드 수정 없이 .env만 변경한다.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore",
                                      protected_namespaces=())

    # App
    app_env: str = "local"
    api_port: int = 8000

    # LLM
    llm_backend: str = "mock"            # mock | llama_cpp
    model_path: str = "./models/model.gguf"
    llm_n_ctx: int = 2048
    llm_n_threads: int = 2
    llm_max_tokens: int = 256
    llm_temperature: float = 0.3
    llm_max_concurrency: int = 1     # EC2 Free Tier 보수 기본값

    # Retriever
    retriever_backend: str = "null"      # null | bm25 | embedding | hybrid
    spec_index_path: str = "./data/index/spec_bm25.pkl"
    doc_index_path: str = "./data/index/docs_bm25.pkl"
    retriever_top_k: int = 3

    # Policy
    rules_path: str = "./rules/safety_spec.yaml"

    # Storage
    db_path: str = "./data/finguard.db"

    # Classifier
    classifier_backend: str = "keyword"      # keyword | (향후) ml | llm
    domain_keywords_path: str = "./rules/domain_keywords.yaml"
    # Rewriter
    templates_path: str = "./rules/rewrite_templates.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()
