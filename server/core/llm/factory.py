from server.config import Settings
from server.core.llm.base import LLMEngine
from server.core.llm.mock_engine import MockEngine
from server.core.llm.llama_cpp_engine import LlamaCppEngine


def create_llm_engine(settings: Settings) -> LLMEngine:
    if settings.llm_backend == "mock":
        return MockEngine()
    if settings.llm_backend == "llama_cpp":
        return LlamaCppEngine(
            model_path=settings.model_path,
            n_ctx=settings.llm_n_ctx,
            n_threads=settings.llm_n_threads,
            max_concurrency=settings.llm_max_concurrency,
        )

    raise ValueError(f"Unknown LLM_BACKEND: {settings.llm_backend}")
