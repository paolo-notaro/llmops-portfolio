"""FastAPI application for the local LLMOps demo."""

from __future__ import annotations

import json
from functools import lru_cache

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from llmops_portfolio.config import REPO_ROOT, Settings, load_settings
from llmops_portfolio.evaluators import evaluate_examples
from llmops_portfolio.models import (
    DocumentSummary,
    EvaluationExample,
    EvaluationReport,
    QueryRequest,
    QueryResponse,
    QueryTrace,
    RetrievedDocument,
)
from llmops_portfolio.observability import metrics_registry
from llmops_portfolio.providers import LLMProvider, provider_from_env
from llmops_portfolio.rag import LocalTfidfRAGIndex


FRONTEND_DIR = REPO_ROOT / "frontend"
DOCS_DIR = REPO_ROOT / "docs"

app = FastAPI(title="LLMOps Portfolio API", version="0.1.0")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")
app.mount("/portfolio-docs", StaticFiles(directory=DOCS_DIR), name="portfolio-docs")

_latest_trace = QueryTrace()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once for the API process."""

    return load_settings()


@lru_cache(maxsize=1)
def get_index() -> LocalTfidfRAGIndex:
    """Build the local retrieval index once."""

    return LocalTfidfRAGIndex.from_directory(get_settings().docs_dir)


@lru_cache(maxsize=1)
def get_provider() -> LLMProvider:
    """Create the configured provider once."""

    return provider_from_env(get_settings().llm_provider)


@lru_cache(maxsize=1)
def get_evaluation_examples() -> tuple[EvaluationExample, ...]:
    """Load local JSONL evaluation examples."""

    examples: list[EvaluationExample] = []
    for path in sorted(get_settings().eval_dir.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip():
                examples.append(EvaluationExample(**json.loads(line)))
            else:
                raise ValueError(f"Blank line in {path}:{line_number}")
    return tuple(examples)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    """Serve the portfolio demo selector."""

    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app", include_in_schema=False)
def customer_app() -> FileResponse:
    """Serve the customer-facing RAG assistant."""

    return FileResponse(FRONTEND_DIR / "app.html")


@app.get("/ops", include_in_schema=False)
def ops_console() -> FileResponse:
    """Serve the LLMOps / DevOps console."""

    return FileResponse(FRONTEND_DIR / "ops.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Avoid noisy favicon 404s in browser demos."""

    return Response(status_code=204)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check."""

    return {"status": "ok", "provider": get_provider().name}


@app.get("/documents", response_model=list[DocumentSummary])
def documents() -> list[DocumentSummary]:
    """Return metadata for the synthetic documents in the local index."""

    return get_index().document_summaries


@app.get("/evaluation/report", response_model=EvaluationReport)
def evaluation_report() -> EvaluationReport:
    """Run the synthetic evaluation suite and return a report for the Ops console."""

    settings = get_settings()
    provider = get_provider()
    return evaluate_examples(
        list(get_evaluation_examples()),
        get_index(),
        provider,
        top_k=3,
        max_latency_ms=settings.max_latency_ms,
        config={
            "provider": provider.name,
            "docs_dir": str(settings.docs_dir),
            "eval_dir": str(settings.eval_dir),
            "top_k": 3,
            "max_latency_ms": settings.max_latency_ms,
            "mode": "api_live_summary",
        },
    )


@app.get("/trace/latest", response_model=QueryTrace)
def latest_trace() -> QueryTrace:
    """Return the latest query trace for the Ops console."""

    return _latest_trace


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    """Retrieve context and generate an answer."""

    global _latest_trace
    retrieved_docs = get_index().query(request.query, top_k=request.top_k)
    response = get_provider().generate(request.query, retrieved_docs)
    quality_checks = _quality_checks(response.answer, response.latency_ms, retrieved_docs)
    metrics_registry.record_request(
        response.latency_ms,
        evaluation_passed=all(quality_checks.values()),
        retrieval_hit=quality_checks["retrieval_hit"],
    )
    _latest_trace = QueryTrace(
        query=request.query,
        answer=response.answer,
        provider=response.provider,
        latency_ms=response.latency_ms,
        retrieved_docs=retrieved_docs,
        quality_checks=quality_checks,
    )
    return QueryResponse(
        answer=response.answer,
        provider=response.provider,
        latency_ms=response.latency_ms,
        retrieved_docs=retrieved_docs,
        quality_checks=quality_checks,
    )


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    """Return Prometheus-style metrics text."""

    return metrics_registry.render_prometheus()


def _quality_checks(answer: str, latency_ms: float, retrieved_docs: list[RetrievedDocument]) -> dict[str, bool]:
    """Compute lightweight live quality signals for an interactive query."""

    lower_answer = answer.lower()
    retrieval_hit = bool(retrieved_docs and retrieved_docs[0].score > 0)
    refusal = "cannot help" in lower_answer
    citation_present = "[doc:" in answer
    return {
        "retrieval_hit": retrieval_hit,
        "citation_or_refusal": citation_present or refusal,
        "grounded_when_answered": refusal or citation_present,
        "latency_under_threshold": latency_ms <= get_settings().max_latency_ms,
    }
