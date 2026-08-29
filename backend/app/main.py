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
from backend.app.database import ensure_tables, check_connection, tables_ready, SessionLocal
from backend.app.seed import maybe_seed, is_seeded
from backend.app.routes import auth, upload, invoices, reports, validation, duplicates

setup_logging(settings.log_level)
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: log boot, ensure DB tables, auto-seed if empty."""
    logger.info(
        "Starting %s v%s (%s environment)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    # Production-readiness: create any missing tables (never crash on a gap),
    # then offer automatic development seeding only when the DB is empty.
    try:
        ok = ensure_tables()
        if not ok:
            logger.warning("Database tables are not fully ready; read endpoints will return empty data.")
        else:
            logger.info("Database initialised (tables ready).")
        # Auto-seed only touches an empty database; existing data is preserved.
        try:
            db = SessionLocal()
            try:
                maybe_seed(db)
            finally:
                db.close()
        except Exception as exc:  # pragma: no cover - infra dependent
            logger.warning("Seed step could not complete: %s", exc)
    except Exception as exc:  # pragma: no cover - infra dependent
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
    """Uptime / load-balancer health check with database status.

    Always returns HTTP 200 while the API process is alive. If the database is
    unavailable the API keeps running and the reason is surfaced in the payload
    (never a raw stack trace).
    """
    db_ok = check_connection()
    ready = db_ok and tables_ready()
    seed_flag = False
    if db_ok:
        try:
            db = SessionLocal()
            try:
                seed_flag = is_seeded(db)
            finally:
                db.close()
        except Exception:  # pragma: no cover - infra dependent
            seed_flag = False

    payload = {
        "status": "running",
        "service": settings.app_name,
        "database": "connected" if db_ok else "unavailable",
        "tables": "ready" if ready else "missing",
        "seed_data": seed_flag,
    }
    if not db_ok:
        payload["reason"] = "Database connection failed — check DATABASE_URL and that the server is running."
    elif not ready:
        payload["reason"] = "One or more required tables are missing — they are created automatically on startup."
    return payload


@app.get("/api/health", tags=["health"])
def api_health_alias():
    """Backward-compatible alias of /health for the frontend Settings page."""
    return health()