from fastapi import APIRouter, Request
from server.config import get_settings
from server.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    s = get_settings()
    llm = request.app.state.llm
    return HealthResponse(
        status="ok" if llm.is_ready() else "degraded",
        app_env=s.app_env,
        llm_backend=s.llm_backend,
        llm_ready=llm.is_ready(),
        llm_error=llm.load_error(),
        model_load_seconds=llm.load_seconds(),
        retriever_backend=s.retriever_backend,
    )


@router.get("/rules")
def rules(request: Request) -> dict:
    policy = request.app.state.policy
    return {"count": policy.rule_count(), "rules": policy.list_rules()}
