"""
Invoice Error Detector — FastAPI application entry point (Phase 1: foundation).

Responsibilities:
  - set up application logging
  - enable CORS for the React frontend
  - initialise the database on startup (non-fatal if unavailable)
  - log every HTTP request (method, path, status, duration)
  - expose /health for uptime/load-balancer checks

Run:
    cd invoice-error-detector
    python -m venv backend/.venv
    backend/.venv/Scripts/pip install -r backend/requirements.txt
    backend/.venv/Scripts/uvicorn backend.app.main:app --reload
    open http://127.0.0.1:8000/docs
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.logging_config import setup_logging, get_logger
from backend.app.database import init_db
from backend.app.routes import auth, upload, invoices, reports, validation, duplicates

setup_logging(settings.log_level)
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: log boot and initialise the database."""
    logger.info(
        "Starting %s v%s (%s environment)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    try:
        init_db()
        logger.info("Database initialised")
    except Exception as exc:  # pragma: no cover - depends on infra
        logger.warning("Database unavailable at startup: %s. API runs; DB features disabled.", exc)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="AI-powered financial validation system for invoices",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Allow the React frontend (via Vite at :5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing routers (upload, invoices, reports, auth — later phases)
for _router in (auth.router, upload.router, invoices.router, reports.router, validation.router, duplicates.router):
    app.include_router(_router)


@app.middleware("http")
async def access_log(request: Request, call_next):
    """Logs every request with its status code and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health", tags=["health"])
def health():
    """Uptime / load-balancer health check."""
    return {"status": "running", "service": settings.app_name}


@app.get("/api/health", tags=["health"])
def api_health_alias():
    """Backward-compatible alias of /health for the frontend Settings page."""
    return health()