"""
Database layer (Phase 1: foundation; Phase 6.1: production readiness).

Connects to MySQL via SQLAlchemy + PyMySQL using the DSN from settings
(`DATABASE_URL`, see .env.example). Swapping backends (e.g. SQLite for local
zero-setup dev) is a one-line environment change and requires no code edits.

Engine is created lazily; a pool_pre_ping + pool_recycle guard against stale
MySQL connections sitting behind proxies/lb.

Production-readiness additions (Phase 6.1):
  - detect missing tables and create them on demand
  - expose `table_exists`, `missing_tables`, `ensure_tables`, `tables_ready`
  - never crash application startup because of a database gap
"""
import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import settings

logger = logging.getLogger("invoice.db")

# sqlite needs a special connection flag; MySQL does not
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else None

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=settings.db_echo,
    **({"connect_args": connect_args} if connect_args else {}),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Tables managed by the app (registered by importing the model modules).
_ALL_TABLES = [
    "companies",
    "vendors",
    "upload_batches",
    "invoices",
    "invoice_items",
    "validation_results",
]


def _import_models() -> None:
    """Import models so they register with `Base.metadata`."""
    from backend.app.models import (  # noqa: F401
        company,
        vendor,
        upload_batch,
        invoice,
        invoice_item,
        validation_result,
    )


def init_db() -> None:
    """Create all tables (idempotent — never drops existing data)."""
    _import_models()
    Base.metadata.create_all(bind=engine)


def table_exists(name: str) -> bool:
    """Return True if the named table currently exists in the database."""
    try:
        with engine.connect() as conn:
            return inspect(conn).has_table(name)
    except Exception:  # pragma: no cover - infra dependent
        logger.warning("Could not check table '%s' existence: DB unavailable.", name)
        return False


def missing_tables() -> list[str]:
    """Return the list of required tables that are not yet present."""
    return [name for name in _ALL_TABLES if not table_exists(name)]


def tables_ready() -> bool:
    """True when every required table exists and is queryable."""
    missing = missing_tables()
    if missing:
        logger.warning("Database tables are incomplete. Missing: %s", ", ".join(missing))
        return False
    return True


def ensure_tables() -> bool:
    """Create any missing tables and report what changed.

    Returns True if all required tables are present afterwards. Logs a
    meaningful message for each missing table that is (re)created, or a
    warning if the table still cannot be created.
    """
    missing = missing_tables()
    if not missing:
        logger.info("All database tables are present (%d).", len(_ALL_TABLES))
        return True

    logger.warning("Detected %d missing table(s): %s. Creating them now.",
                   len(missing), ", ".join(missing))
    _import_models()
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover - infra dependent
        logger.error("Failed to create missing tables (%s).", exc)
        return False

    still_missing = missing_tables()
    if still_missing:
        logger.warning("Tables could not be created: %s", ", ".join(still_missing))
        return False
    logger.info("Created missing tables successfully: %s", ", ".join(missing))
    return True


def check_connection() -> bool:
    """Round-trip SELECT 1 to confirm the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_db():
    """FastAPI dependency: yields a session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def read_guard(rows_factory, empty=()):
    """Yield rows from `rows_factory` or fall back to an empty result.

    Used by read-only endpoints so an empty / temporarily-unavailable database
    never surfaces as HTTP 500 — the API returns an empty collection and logs
    the underlying reason (stack traces are never forwarded to the client).
    """
    try:
        return rows_factory()
    except Exception as exc:  # pragma: no cover - infra dependent
        logger.warning("Database read failed; returning empty result (%s).", exc)
        return empty