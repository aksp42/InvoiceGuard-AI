"""
Application configuration (Phase 1: foundation).

Central, typed settings loaded via pydantic-settings from environment
variables or the `backend/.env` file. Every value can be overridden at
runtime without touching code — the standard 12-factor approach.

Kept forward-compatible: module-level aliases below mirror the previous
flat names so later-phase modules (services, auth) keep working unchanged.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = invoice-error-detector/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# backend/.env lives next to this file
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings. Field names map to UPPER_CASE env vars."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Invoice Error Detector API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # --- Database (MySQL by default; see .env.example) ---
    database_url: str = "mysql+pymysql://root:root@localhost:3306/invoice_db?charset=utf8mb4"
    db_echo: bool = False

    # --- CORS: allowed frontend origins (comma-separated) ---
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Validation rules (used in later phases) ---
    price_outlier_threshold: float = 3000.0
    amount_tolerance: float = 1.0

    # --- Upload security (Phase 3.1) ---
    max_upload_size_mb: int = 20

    # --- ML engine artefacts (used in later phases) ---
    ml_enabled: bool = True
    model_path: Path = BASE_DIR / "ml_engine" / "model.pkl"
    scaler_path: Path = BASE_DIR / "ml_engine" / "scaler.pkl"

    # --- Demo authentication (used in later phases) ---
    demo_user: str = "admin"
    demo_password: str = "admin123"

    # --- Auto-seed (Phase 6.1: production readiness) ---
    # When true and the database has no invoices, sample data is inserted once
    # at startup. Existing data is NEVER overwritten.
    auto_seed: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse the comma-separated origins string into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum accepted upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()

# ---------------------------------------------------------------------------
# Compatibility aliases for existing modules (unchanged import behaviour)
# ---------------------------------------------------------------------------
DATABASE_URL = settings.database_url
ALLOWED_ORIGINS = settings.cors_origin_list
PRICE_OUTLIER_THRESHOLD = settings.price_outlier_threshold
AMOUNT_TOLERANCE = settings.amount_tolerance
ML_ENABLED = settings.ml_enabled
MODEL_PATH = str(settings.model_path)
SCALER_PATH = str(settings.scaler_path)
DEMO_USER = settings.demo_user
DEMO_PASSWORD = settings.demo_password