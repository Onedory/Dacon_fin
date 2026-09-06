from fastapi import APIRouter, Request
from server.schemas import AnalyzeRequest, AnalyzeResponse
from fastapi import APIRouter, HTTPException, Request
router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    llm = request.app.state.llm
    if not llm.is_ready():
        raise HTTPException(status_code=503,
            detail=f"LLM 미준비: {llm.load_error() or 'unknown'}")
    return request.app.state.orchestrator.run(req)
