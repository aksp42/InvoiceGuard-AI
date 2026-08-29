# Changelog

All notable changes to **InvoiceGuard-AI** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned

- **OCR ingestion** — PDF / scanned-invoice ingestion (Phase 7 roadmap).
- **Price-anomaly & vendor-fraud detection**, payment reconciliation.
- **Email alerts** & real-time webhooks.
- **ERP integration** (SAP / Tally / Zoho).
- **Docker Compose deployment** + CI/CD pipelines.

---

## [1.0.0] - 2026-08-29

### 🎉 Initial production release

The first stable release of the Invoice Guard-AI platform — a complete,
deployable invoice validation and duplicate-detection system.

#### Added

- **FastAPI backend**
  - Env-driven 12-factor configuration (`config.py`) with CORS + access logging.
  - Startup lifecycle that creates missing tables and auto-seeds an empty DB.
  - Expanded `/health` reporting database, table and seed readiness.
- **Frontend (React + Vite)**
  - SPA with login, dashboard KPIs, high-risk triage, invoice drill-down,
    duplicates review, reports and settings.
  - **Executive Analytics Dashboard** (5 pages): Executive Overview, Vendor
    Intelligence, Validation Insights, Duplicate Intelligence, Audit Center —
    with shared data hook, retry-on-error banners and graceful empty-state handling.
- **Secure Upload Pipeline**
  - CSV / XLSX parsing with streaming 20 MB size cap.
  - Extension + MIME allow-lists, Excel magic-byte sniffing, filename sanitisation.
  - Transactional batch integrity (nested savepoint, whole-upload rollback).
  - Full upload audit log (`backend/logs/upload_audit.log`).
- **Validation Engine**
  - Deterministic rule-based checks: GST/amount mismatch, negative amounts,
    invalid quantity/unit price, missing fields, future dates.
  - Per-invoice issues with machine-readable codes.
- **Duplicate Detection Intelligence**
  - 5-level matching: exact, vendor, near, date-window, line-item.
  - Confidence scores, similarity, severity and idempotent risk penalties.
- **ML Risk Engine**
  - Isolation-Forest anomaly scoring (scikit-learn, joblib-serialised) blended
    into a single 0–100 `risk_score` + status.
- **Reporting & BI**
  - CSV, Excel and PDF report export.
  - Power BI dashboard (`analytics/powerbi/Invoice_Dashboard.pbix`) + SQL
    analytics queries.
- **Database**
  - MySQL 8 schema (InnoDB / utf8mb4) with indexes and foreign keys.
  - SQLite-compatible development mode; seed data + sample files.
- **Production hardening**
  - Safe read guards (empty responses instead of HTTP 500 on DB failure).
  - Auto-seed on fresh clone (opt-out via `AUTO_SEED`).

#### Documentation

- Premium `README.md` with hero, badges, features, screenshots, architecture,
  install/run steps, API reference, roadmap and license.
- `docs/System_Architecture.md` — Mermaid diagrams for system, upload, validation,
  duplicate detection and dashboard data flow.
- `docs/API_Documentation.md` — full endpoint reference + cURL examples.
- `docs/Portfolio_Case_Study.md` — recruiter-focused write-up.
- `docs/Demo_Guide.md` — 90-second live demo script.
- `docs/Screenshot_Guide.md` — capture plan + naming convention.
- `docs/BRAND.md` + `docs/assets/brand/` — logo, banner, favicon, palette.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue & PR templates, `CHANGELOG.md`.

---

## Versioning

- **Semantic versioning:** `MAJOR.MINOR.PATCH` — backwards-incompatible, feature,
  and patch changes respectively.
- Current release: **v1.0.0**.

---

© 2026 InvoiceGuard-AI · [Back to README](README.md)
