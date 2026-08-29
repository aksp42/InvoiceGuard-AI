"""
Application logging configuration (Phase 1: foundation, Phase 3.1: audit).

Provides:
  - console handler (stdout) for local dev / container logs
  - rotating file handler under backend/logs/app.log (5 MB x 3 backups)
  - rotating upload-audit handler under backend/logs/upload_audit.log with the
    dedicated 'invoice.audit' logger (Phase 3.1), lazily self-configured so
    services can emit audit events even when setup_logging() has not run.

Call setup_logging(log_level) once at application startup.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

_CONSOLE_FMT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_FILE_FMT = "%(asctime)s | %(levelname)-7s | %(name)s | %(module)s:%(lineno)d | %(message)s"
_AUDIT_FMT = "%(asctime)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _console_handler(level: int) -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_CONSOLE_FMT, datefmt=_DATE_FMT))
    return handler


def _file_handler(log_path: Path, level: int) -> logging.Handler:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    return handler


def setup_logging(log_level: str = "INFO", log_dir: Path = LOG_DIR) -> logging.Logger:
    """Configure root logging and return the application logger (name 'invoice')."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers = [_console_handler(level)]
    if log_dir:
        handlers.append(_file_handler(log_dir / "app.log", level))

    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Re-route uvicorn's own logs through our root config to avoid duplicate lines
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn").propagate = True

    if log_dir:
        get_audit_logger(log_dir)

    return get_logger()


def get_logger(name: str = "invoice") -> logging.Logger:
    """Return a logger namespaced under the application logger."""
    return logging.getLogger(name)


def get_audit_logger(log_dir: Path = LOG_DIR) -> logging.Logger:
    """Return the upload-audit logger (name 'invoice.audit').

    Lazily attaches a rotating file handler under backend/logs/upload_audit.log
    so audit events from the upload pipeline are persisted even when
    setup_logging() has not been run (e.g. service-level tests). Guarded by
    `handlers` so repeated calls never attach duplicate handlers.
    """
    logger = logging.getLogger("invoice.audit")
    if not logger.handlers:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_dir / "upload_audit.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(_AUDIT_FMT, datefmt=_DATE_FMT))
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.addHandler(handler)
    return logger