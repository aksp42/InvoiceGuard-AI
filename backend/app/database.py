"""
Database layer (Phase 1: foundation).

Connects to MySQL via SQLAlchemy + PyMySQL using the DSN from settings
(`DATABASE_URL`, see .env.example). Swapping backends (e.g. SQLite for local
zero-setup dev) is a one-line environment change and requires no code edits.

Engine is created lazily; a pool_pre_ping + pool_recycle guard against stale
MySQL connections sitting behind proxies/lb.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import settings

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


def init_db() -> None:
    """Create all tables. Imports models so they register with metadata."""
    from backend.app.models import company, vendor, upload_batch, invoice, invoice_item, validation_result  # noqa: F401

    Base.metadata.create_all(bind=engine)


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