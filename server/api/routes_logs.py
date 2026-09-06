from fastapi import APIRouter, Request
from server.schemas import LogsResponse

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs", response_model=LogsResponse)
def logs(request: Request, limit: int = 50) -> LogsResponse:
    total, items = request.app.state.audit_logger.list_logs(limit)
    return LogsResponse(total=total, items=items)
