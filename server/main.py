from contextlib import asynccontextmanager
from fastapi import FastAPI

from server.config import get_settings
from server.core.llm.factory import create_llm_engine
from server.core.retriever.factory import create_retriever
from server.pipeline.orchestrator import Orchestrator
from server.api import routes_analyze, routes_logs, routes_meta
from server.core.policy.rule_engine import RuleEngine
from server.core.classifier.factory import create_classifier
from server.pipeline.rewriter import TemplateRewriter
# import 추가
from fastapi.staticfiles import StaticFiles
from server.core.logger import AuditLogger

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    llm = create_llm_engine(settings)
    llm.load()

    spec_retriever = create_retriever(settings, settings.spec_index_path)
    doc_retriever = create_retriever(settings, settings.doc_index_path)
    spec_retriever.load_index()
    doc_retriever.load_index()

    policy = RuleEngine(settings.rules_path)
    policy.load_rules()

    classifier = create_classifier(settings)
    classifier.load()

    rewriter = TemplateRewriter(settings.templates_path,
                                policy.rewrite_template_map())
    rewriter.load()

    audit_logger = AuditLogger(settings.db_path)          # ①

    app.state.llm = llm
    app.state.policy = policy
    app.state.audit_logger = audit_logger
    app.state.orchestrator = Orchestrator(
        settings=settings, llm=llm,
        spec_retriever=spec_retriever, doc_retriever=doc_retriever,
        policy=policy, classifier=classifier, rewriter=rewriter,
        audit_logger=audit_logger,                        # ② 이게 빠졌을 가능성 높음!
    )
    yield
    audit_logger.close()                                  # ③ 종료 시 연결 해제


def create_app() -> FastAPI:
    app = FastAPI(title="FinGuard AI", version="0.1.0", lifespan=lifespan)
    app.include_router(routes_meta.router)
    app.include_router(routes_analyze.router)
    app.include_router(routes_logs.router)
    # create_app(): 라우터 등록 뒤 마지막 줄에 정적 마운트 (반드시 라우터 이후!)
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    return app


app = create_app()
