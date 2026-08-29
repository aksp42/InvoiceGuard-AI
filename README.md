<div align="center">

<!-- Hero banner / social preview -->
<img src="docs/assets/brand/banner.svg" alt="InvoiceGuard-AI banner" width="100%">

<br/>

# 🛡️ InvoiceGuard-AI

**Catch it before you pay it.** AI-assisted invoice validation &amp; duplicate-detection engine that stops duplicate submissions, wrong totals, GST mismatches and missing fields before a single invoice reaches your ledger.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?logo=powerbi&logoColor=000)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikit-learn&logoColor=white)
![Version](https://img.shields.io/badge/version-v1.0.0-3B82F6)
![Build Ready](https://img.shields.io/badge/build-ready-22C55E)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**Deterministic rule engine · 5-level duplicate intelligence · Isolation-Forest risk scoring · Power BI analytics**

</div>

---

## 📖 Overview

### The problem

Finance teams lose millions to **duplicate** and **fraudulent** invoices — often silently. Vendors resubmit the same bill twice, line items get double-counted, GST is miscalculated, and amounts drift from their source documents. Manually reviewing every line item doesn't scale, and pure-ML approaches are hard to trust and explain.

### What InvoiceGuard-AI does

InvoiceGuard-AI turns the messy, high-risk act of **invoice intake** into a deterministic, auditable, explainable pipeline. Every uploaded invoice is:

1. **Parsed** safely (CSV / XLSX) into a transactional batch.
2. **Validated** against hard business rules (GST/amount mismatch, negative values, missing fields, future dates).
3. **Checked for duplicates** across five escalating confidence levels.
4. **Risk-scored** by blending rule findings with an Isolation-Forest anomaly signal into one actionable 0–100 score.
5. **Reported** to the dashboard, a drill-down UI, an audit log, CSV/Excel/PDF exports, and a **Power BI** dashboard.

### Why it matters

The system is **explainable** (every flag carries a rule + confidence score) yet **powerful** (ML surfaces anomalies that fixed rules miss) and **production-safe** (transactional uploads, never a 500 on a missing table, full audit trail).

### Target users

- **Accounts payable** teams reviewing, triaging and paying invoices.
- **Finance leaders** who need a live executive dashboard over risk exposure.
- **Developers** building financial validation into larger ERPs / workflows.

---

## ✨ Features

### 📤 Secure Upload Pipeline
- CSV / XLSX parsing with **20 MB streaming size cap** (files are never fully buffered)
- Extension + MIME allow-list, **magic-byte sniffing** for Excel, sanitised filenames
- **Transactional batch integrity** — one atomic transaction per upload, rollback on failure
- Full **upload audit log** (`backend/logs/upload_audit.log`)

### 🩺 Rule-Based Validation Engine
- Hard business rules: GST/amount mismatch, negative amounts, invalid quantity/unit price, empty product names, future dates
- Per-invoice issue list with machine-readable codes

### 🔁 5-Level Duplicate Detection Intelligence
- **L1 Exact** · **L2 Vendor** · **L3 Near** · **L4 Date-window** · **L5 Line-item** matching
- RapidFuzz fuzzy matching with **confidence scores** and idempotent risk penalties

### 🧠 ML Risk Scoring
- **Isolation Forest** anomaly score over amount, quantity, unit price and vendor-relative pricing
- Blended with rule findings into a single `risk_score` (0–100) and final status

### 📊 Executive Analytics Dashboard
- **Executive Overview · Vendor Intelligence · Validation Insights · Duplicate Intelligence · Audit Center** (5 pages)
- Resilience built-in: retry-on-error banners, graceful empty-database handling

### 🛡️ Production Readiness
- Safe DB initialisation — missing tables auto-created, **empty reads never crash**
- **Auto-seed** on a fresh clone; expanded `/health`; never a stack trace to the client

### 📑 Enterprise Reporting & BI
- CSV / Excel / PDF report export
- **Power BI** dashboard (`analytics/powerbi/Invoice_Dashboard.pbix`) + SQL queries

---

## 📸 Screenshots

> See `docs/Screenshot_Guide.md` for the capture checklist, ideal browser size and
> naming convention. Screenshots below live in `screenshots/`.

<div align="center">

**Marketing / portfolio**
| | |
|---|---|
| **Dashboard** | **Upload** |
| ![Dashboard](screenshots/dashboard.png) | ![Upload](screenshots/upload.png) |
| **High Risk Triage** | **Invoice Details** |
| ![High Risk](screenshots/high_risk.png) | ![Invoice Details](screenshots/invoice_details.png) |
| **Reports** | |
| ![Reports](screenshots/reports.png) | |

</div>

> Suggested captures for the analytics pages (see [Screenshot Guide](docs/Screenshot_Guide.md)):
> `executive-overview.png`, `vendor-intelligence.png`, `validation-insights.png`,
> `duplicate-intelligence.png`, `audit-center.png`.

---

## 🏗 Architecture

```
 ┌────────────────┐         ┌──────────────────────────────┐         ┌──────────────┐
 │  React + Vite  │   HTTP  │          FastAPI             │  SQLAlchemy │   MySQL 8    │
 │  (5173)        │ ──────► │  routes/  services/  models  │ ─────────► │  invoice_db  │
 │  SPA           │   JSON  │                              │             └──────────────┘
 └────────────────┘         │  upload / validation /       │
                            │  duplicates / reports / auth │
                            └──────────────────────────────┘
                                      │  joblib
                                      ▼
                            ┌──────────────────────┐
                            │   Isolation Forest   │   ← ML anomaly engine
                            │   ml_engine/         │
                            └──────────────────────┘
```

Full diagrams (system, upload flow, validation flow, duplicate flow, dashboard
data flow) with Mermaid render in **[docs/System_Architecture.md](docs/System_Architecture.md)**.

### Data flow (condensed)

1. **Upload** → `POST /api/upload/*` (CSV/XLSX), parsed & stored transactionally in a batch.
2. **Validate** → `POST /api/validate/{batch_id}` runs the deterministic rule engine.
3. **Duplicate scan** → `POST /api/duplicates/{batch_id}` runs the 5-level matcher.
4. **Risk blend** → `risk_service` fuses rule findings + ML anomaly + duplicate penalties.
5. **Report & act** → review in the UI, export reports, or load the Power BI dashboard.

---

## 🔁 Duplicate Detection Levels

| Level | Name | Detection logic | Severity | Confidence | Risk |
|:-----:|------|-----------------|:--------:|:----------:|:----:|
| L1 | **Exact** | Same company + identical invoice number | CRITICAL | 100% | +50 |
| L2 | **Vendor** | Same vendor + amount + date | CRITICAL | 98% | +40 |
| L3 | **Near** | Same vendor + number sim ≥90% + amount ≤₹1 | ERROR | 95% | +30 |
| L4 | **Date** | Same vendor + amount within 3 days | WARNING | 85% | +15 |
| L5 | **Item** | Identical line-item multiset (order-insensitive) | ERROR | 92% | +25 |

Findings persist into `validation_results` with a populated `confidence_score`;
penalties apply once per pair (idempotent on re-scan); risk is clamped to 100.

---

## 🗂 Folder Structure

```
invoice-error-detector/
├── README.md                       # You are here
├── LICENSE                         # MIT
├── CHANGELOG.md                    # Semantic version history
├── CONTRIBUTING.md                 # Contribution guide
├── CODE_OF_CONDUCT.md
├── .github/                        # Issue & PR templates
│   └── ISSUE_TEMPLATE/
├── docker-compose.yml              # (Future) containerised stack
│
├── frontend/                       # React + Vite SPA
│   └── src/
│       ├── components/             # Navbar, Sidebar, KPI_Card, InvoiceTable, UploadBox, RiskBadge, ...
│       ├── pages/                  # Login, Dashboard, UploadInvoices, InvoiceDetails, HighRisk, Reports, ...
│       ├── analytics/              # 5-page executive dashboard (Phase 6)
│       │   ├── pages/              # ExecutiveOverview, VendorIntelligence, ValidationInsights,
│       │   │                       #   DuplicateIntelligence, AuditCenter
│       │   ├── components/         # AnalyticsShell, charts, ErrorBanner, AnimatedCounter
│       │   └── lib/                # useAnalyticsData (data hook + retry)
│       └── services/api.js         # REST API client
│
├── backend/                        # FastAPI service
│   └── app/
│       ├── main.py                 # Entry point, lifespan, /health
│       ├── config.py               # Env-driven typed settings (12-factor)
│       ├── database.py             # SQLAlchemy engine / session / safe-read guards
│       ├── seed.py                 # Auto-seed on empty DB (Phase 6.1)
│       ├── schemas.py              # Pydantic request/response models
│       ├── routes/                 # auth, upload, invoices, validation, duplicates, reports
│       ├── services/               # validation, duplicate_*, risk, tax, report, upload
│       ├── models/                 # Vendor, Invoice, InvoiceItem, UploadBatch, ValidationResult
│       └── utils/                  # csv_reader, excel_reader, pdf_export
│
├── ml_engine/                      # scikit-learn Isolation Forest
│   ├── feature_engineering.py
│   ├── anomaly_detection.py
│   ├── train_model.py              # → builds model.pkl + scaler.pkl
│   └── predict.py                  # scoring entry point
│
├── database/
│   ├── schema.sql                  # MySQL schema (InnoDB / utf8mb4)
│   ├── seed_data.sql
│   ├── sample_invoices.csv
│   └── sample_bulk_upload.xlsx
│
├── analytics/
│   ├── powerbi/                    # Invoice_Dashboard.pbix + Dashboard_Guide.pdf
│   └── sql_queries/                # duplicate_invoices, vendor_analysis, high_risk, monthly_trends
│
├── reports/                        # sample export files
├── screenshots/                    # dashboard, upload, high_risk, invoice_details, reports
└── docs/
    ├── BRAND.md                    # Color palette & brand guidelines
    ├── System_Architecture.md      # Mermaid architecture diagrams
    ├── API_Documentation.md        # Full endpoint reference
    ├── Database_Design.md / .pdf
    ├── ER_Diagram.png
    ├── Workflow_Diagram.png
    ├── Portfolio_Case_Study.md
    ├── Demo_Guide.md
    ├── Screenshot_Guide.md
    ├── Quality_Audit_Report.md
    └── Project_Report.docx
```

---

## 🛠 Tech Stack

| Layer        | Technology |
|--------------|------------|
| **Frontend** | React 18, Vite 5, React Router 6, CSS |
| **Backend**  | FastAPI 0.115, Uvicorn, SQLAlchemy 2.0 (ORM), Pydantic v2 |
| **Database** | MySQL 8.0 (InnoDB / utf8mb4) · SQLite out-of-the-box for dev |
| **Validation** | Custom deterministic rule engine + RapidFuzz fuzzy matching |
| **ML-ready** | scikit-learn Isolation Forest (joblib-serialised), pandas, openpyxl |
| **BI**       | Power BI dashboard + raw SQL analytics queries |
| **Ops**      | 12-factor env config, CORS, Docker Compose (planned) |

See [`backend/requirements.txt`](backend/requirements.txt) for pinned versions.

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm`
- **MySQL 8.0** (optional — SQLite is used by default for a quick start)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Copy the env template (adjust credentials / DATABASE_URL as needed)
copy backend\.env.example backend\.env        # Windows
# cp backend/.env.example backend/.env        # macOS/Linux
```

> On first run with an empty database the API **auto-creates tables and seeds
> sample data** (set `AUTO_SEED=false` in `.env` to disable).

### 2. Run the backend

```bash
uvicorn backend.app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger docs, or
**http://127.0.0.1:8000/health** for a live health check.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and log in with `admin` / `admin123`.

### 4. MySQL (optional, production)

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p invoice_db < database/seed_data.sql
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/invoice_db?charset=utf8mb4"
```

No code changes are required to switch databases — configuration is fully env-driven.

### 5. Train the ML model (optional)

```bash
python -m ml_engine.train_model --data database/sample_invoices.csv
```

Writes `ml_engine/model.pkl` + `ml_engine/scaler.pkl`. If the artefacts are absent,
`ml_engine/predict.py` falls back to fitting Isolation Forest on the incoming batch.

---

## 🔌 API Documentation

Interactive docs at **`http://127.0.0.1:8000/docs`** (Swagger). Full reference,
request/response bodies, status codes and cURL examples in
**[docs/API_Documentation.md](docs/API_Documentation.md)**.

> All routes are prefixed with `/api`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/health` · `/api/health` | Live health / DB readiness check |
| `POST` | `/api/auth/login` | Demo auth — returns a bearer token |
| `POST` | `/api/upload/single` | Upload a single-invoice CSV |
| `POST` | `/api/upload/bulk` | Bulk CSV / XLSX upload (transactional) |
| `GET`  | `/api/upload/history` | List recent upload batches |
| `GET`  | `/api/upload/{batch_id}` | Batch detail incl. its invoices |
| `GET`  | `/api/invoices` | List invoices |
| `GET`  | `/api/invoices/{invoice_id}` | Single invoice with items + findings |
| `POST` | `/api/validate/{batch_id}` | Run the rule-based validation engine |
| `POST` | `/api/duplicates/{batch_id}` | Run 5-level duplicate detection |
| `GET`  | `/api/duplicates` | Deduplicated duplicate pairs |
| `GET`  | `/api/report/csv` | Download validation report (CSV) |
| `GET`  | `/api/report/excel` | Download validation report (XLSX) |
| `GET`  | `/api/report/pdf` | Download validation report (PDF) |

### Quick start — upload &amp; validate

```bash
# Upload a batch
curl -F "file=@database/sample_invoices.csv" http://127.0.0.1:8000/api/upload/bulk

# Validate it (batch_id comes from the upload response)
curl -X POST http://127.0.0.1:8000/api/validate/1

# Scan for duplicates
curl -X POST http://127.0.0.1:8000/api/duplicates/1

# List duplicate pairs
curl http://127.0.0.1:8000/api/duplicates
```

---

## 🧪 How Risk Scoring Works

1. **Rule engine** (`services/validation_service.py`) enforces hard business rules —
   duplicate ID, GST/amount mismatch, negative amounts, invalid quantity/unit price,
   empty product names, future dates.
2. **ML model** (`ml_engine/`) runs an **Isolation Forest** over amount, quantity,
   unit price and vendor-relative pricing to catch anomalies fixed rules miss
   (an invoice that's individually *valid* but priced far outside the vendor's history).
3. **`risk_service.py`** blends both into a single 0–100 score and final status —
   a GST mismatch or flagged duplicate always forces `High Risk` / `Critical`.

**Invoice statuses:** `Pending` · `Valid` · `Needs Review` · `High Risk` · `Critical` · `Duplicate` · `Paid`

---

## 🛣 Roadmap

### Completed

- [x] **Phase 1** — FastAPI foundation, config, CORS, health
- [x] **Phase 2** — MySQL schema, models, SQLite-compatible dev DB
- [x] **Phase 3** — Secure CSV/XLSX upload pipeline + audit logging
- [x] **Phase 4** — Rule-based validation engine
- [x] **Phase 5** — Duplicate detection intelligence (5-level match + confidence)
- [x] **Phase 6** — Executive analytics dashboard (5 pages) + Power BI
- [x] **Phase 6.1** — Production readiness: auto-seed, safe reads, resilience

### Future

- [ ] **Phase 7** — PDF / OCR invoice ingestion
- [ ] **Phase 8** — Price-anomaly & vendor-fraud detection, payment reconciliation
- [ ] **Phase 9** — Email alerts & real-time webhooks
- [ ] **Phase 10** — ERP integration (SAP / Tally / Zoho)
- [ ] **Phase 11** — Docker Compose deployment + CI/CD pipelines

---

## 🤝 Contributing

Contributions are welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for our
standards and **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**, and use the issue/PR
templates under [`.github/`](.github/).

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Commit your changes
4. Open a pull request with the provided template

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 🧭 Portfolio & Demo

- **90-second demo script & talking points** → [`docs/Demo_Guide.md`](docs/Demo_Guide.md)
- **Recruiter-focused case study** → [`docs/Portfolio_Case_Study.md`](docs/Portfolio_Case_Study.md)
- **Brand & assets** → [`docs/BRAND.md`](docs/BRAND.md)

---

<div align="center">

Built with ❤️ using **FastAPI, React, MySQL & scikit-learn**.

**Report · Review · Pay with confidence.**

</div>
