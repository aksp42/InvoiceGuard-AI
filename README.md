<div align="center">

# 🛡️ InvoiceGuard-AI

**Enterprise-grade, AI-assisted invoice validation & duplicate detection engine.**
Catches duplicate submissions, wrong totals, GST mismatches, missing fields and
price anomalies before a single invoice reaches payment — then layers an
Isolation-Forest risk score on top.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](backend/requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?logo=fastapi&logoColor=white)](backend/requirements.txt)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](frontend/package.json)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)](frontend/package.json)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](database/schema.sql)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?logo=scikit-learn&logoColor=white)](ml_engine)

**Deterministic rule engine · 5-level duplicate detection · ML anomaly risk · Power BI analytics**

</div>

---

## ✨ Features

- **🔁 5-Level Duplicate Detection Intelligence** — deterministic matching that finds
  exact, near, vendor, date-window and line-item-level duplicates without OCR or ML.
- **🩺 Rule-Based Validation Engine** — hard business rules (GST/amount mismatch,
  negative amounts, invalid quantity/unit price, empty product names, future dates).
- **🧠 Isolation-Forest Risk Scoring** — an anomaly score (0–100) blended with rule
  findings for a single actionable `risk_score` and status badge.
- **📤 Secure Upload Pipeline** — CSV / XLSX parsing with size limits, sanitised
  filenames, transactional batch integrity and full upload audit logging.
- **📊 Enterprise Reporting** — CSV, Excel and PDF report export plus a Power BI
  dashboard over the same data.
- **🔐 Demo Auth + UI** — React SPA with login, dashboard KPIs, high-risk triage,
  per-invoice drill-down and a dedicated duplicate review page.
- **📦 MySQL-Ready** — production InnoDB/utf8mb4 schema with indexes, foreign keys
  and seed data; runs on SQLite out of the box for local development.

---

## 🏗 Architecture

```
 ┌────────────────┐         ┌──────────────────────────────┐         ┌──────────────┐
 │  React + Vite  │  HTTP   │          FastAPI             │  SQLAlchemy │   MySQL 8    │
 │  (5173)        │ ──────► │  routes/  services/  models  │ ─────────► │  invoice_db  │
 │                │  JSON   │                              │            └──────────────┘
 └────────────────┘         │  upload / validation /       │
                            │  duplicates / reports / auth │
                            └──────────────────────────────┘
                                      │  joblib
                                      ▼
                            ┌──────────────────────┐
                            │   Isolation Forest   │
                            │   ml_engine/         │
                            └──────────────────────┘
```

### Data flow

1. **Upload** — invoices land as CSV or XLSX via `POST /api/upload/*`, parsed,
   validated for size/columns, and stored transactionally in a batch.
2. **Validate** — `POST /api/validate/{batch_id}` runs each invoice through the
   **rule engine** (GST/amount, negative values, missing fields, price outliers).
3. **Duplicate scan** — `POST /api/duplicates/{batch_id}` runs the 5-level matcher
   against every invoice of the same company (across all batches).
4. **Risk blend** — `risk_service` fuses rule findings + ML anomaly + duplicate
   penalties into one 0–100 score and a final status.
5. **Report & act** — review in the UI, export CSV/XLSX/PDF, or load the Power BI
   dashboard / SQL queries in `analytics/`.

---

## 🧩 Duplicate Detection Levels

| Level | Name | Detection logic | Severity | Confidence | Risk |
|:-----:|------|-----------------|:--------:|:----------:|:----:|
| L1 | **Exact** | Same company + identical invoice number | CRITICAL | 100% | +50 |
| L2 | **Vendor** | Same vendor + amount + date | CRITICAL | 98% | +40 |
| L3 | **Near** | Same vendor + number sim ≥90% + amount ≤₹1 | ERROR | 95% | +30 |
| L4 | **Date** | Same vendor + amount within 3 days | WARNING | 85% | +15 |
| L5 | **Item** | Identical line-item multiset (order-insensitive) | ERROR | 92% | +25 |

Findings are persisted into `validation_results` with a populated
`confidence_score`, penalties are applied once per pair (idempotent on re-scan),
and risk is clamped to 100.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | [FastAPI](https://fastapi.tiangolo.com) 0.115, Uvicorn |
| **Web** | [React](https://react.dev) 18, [Vite](https://vitejs.dev) 5, React Router 6 |
| **Database** | [MySQL](https://www.mysql.com) 8 (InnoDB / utf8mb4), SQLAlchemy 2.0 ORM |
| **Validation** | Custom deterministic rule engine + [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) fuzzy matching |
| **ML** | [scikit-learn](https://scikit-learn.org) Isolation Forest (joblib-serialised) |
| **Data** | pandas, openpyxl |
| **Reporting** | ReportLab (PDF), pandas/OpenPyXL (Excel), Power BI |
| **Ops** | Docker Compose (future), 12-factor env config |

---

## 🗂 Project Structure

```
invoice-error-detector/
├── README.md
├── LICENSE                          # MIT
├── .gitignore
├── docker-compose.yml               # (Future) containerised stack
│
├── frontend/                       # React + Vite SPA
│   └── src/
│       ├── components/             # Navbar, Sidebar, KPI_Card, InvoiceTable, UploadBox, RiskBadge
│       ├── pages/                  # Login, Dashboard, UploadInvoices, InvoiceDetails, HighRisk,
│       │                           #   Reports, Settings, DuplicateInvoices
│       ├── services/api.js         # API client
│       ├── App.jsx                 # Routes
│       └── main.jsx
│
├── backend/                        # FastAPI service
│   └── app/
│       ├── main.py                 # Entry point (uvicorn backend.app.main:app)
│       ├── config.py               # Env-driven typed settings
│       ├── database.py             # SQLAlchemy engine / session
│       ├── schemas.py              # Pydantic request/response models
│       ├── routes/                 # upload, invoices, validate, duplicates, reports, auth
│       ├── services/               # validation, duplicate_matcher/rules/service,
│       │                           #   tax, risk, report, upload services
│       ├── models/                 # Vendor, Invoice, InvoiceItem, UploadBatch, ValidationResult
│       └── utils/                  # csv_reader, excel_reader, pdf_export
│
├── ml_engine/                      # AI anomaly detection (Isolation Forest)
│   ├── feature_engineering.py
│   ├── anomaly_detection.py
│   ├── train_model.py              # builds model.pkl + scaler.pkl
│   └── predict.py                  # scoring entry point used by the backend
│
├── database/
│   ├── schema.sql                  # MySQL schema (InnoDB / utf8mb4)
│   ├── seed_data.sql               # vendors + sample invoices
│   ├── sample_invoices.csv
│   └── sample_bulk_upload.xlsx
│
├── analytics/
│   ├── powerbi/                    # Invoice_Dashboard.pbix + Dashboard_Guide.pdf
│   └── sql_queries/                # duplicate_invoices, vendor_analysis, high_risk, monthly_trends
│
├── reports/                        # sample_validation_report.pdf, sample_error_report.xlsx,
│                                   #   sample_high_risk_report.csv
├── screenshots/                    # dashboard, upload, high_risk, invoice_details, reports
└── docs/
    ├── Workflow_Diagram.png
    ├── ER_Diagram.png
    ├── Database_Design.md / .pdf
    └── Project_Report.docx
```

---

## 📸 Screenshots

<div align="center">

**Dashboard**
![Dashboard](screenshots/dashboard.png)

| | |
|---|---|
| **Upload** | **High Risk** |
| ![Upload](screenshots/upload.png) | ![High Risk](screenshots/high_risk.png) |
| **Invoice Details** | **Reports** |
| ![Invoice Details](screenshots/invoice_details.png) | ![Reports](screenshots/reports.png) |

</div>

---

## 🔌 API Reference

Interactive docs at **`http://127.0.0.1:8000/docs`** (Swagger) once the server runs.

> All routes are prefixed with `/api`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Demo auth — returns a bearer token (`admin` / `admin123`) |
| `POST` | `/api/upload/single` | Upload a single-invoice CSV |
| `POST` | `/api/upload/bulk` | Bulk CSV / XLSX upload (transactional batch) |
| `GET`  | `/api/upload/history` | List upload batches |
| `GET`  | `/api/upload/{batch_id}` | Batch detail incl. its invoices |
| `GET`  | `/api/invoices` | List invoices |
| `GET`  | `/api/invoices/{invoice_id}` | Single invoice with items + findings |
| `POST` | `/api/validate/{batch_id}` | Run the rule-based validation engine |
| `POST` | `/api/duplicates/{batch_id}` | Run 5-level duplicate detection |
| `GET`  | `/api/duplicates` | Deduplicated duplicate pairs |
| `GET`  | `/api/report/csv` | Download validation report (CSV) |
| `GET`  | `/api/report/excel` | Download validation report (XLSX) |
| `GET`  | `/api/report/pdf` | Download validation report (PDF) |

### Example — upload & validate

```bash
# Upload a batch
curl -F "file=@database/sample_invoices.csv" http://127.0.0.1:8000/api/upload/bulk

# Validate it (batch_id from the response)
curl -X POST http://127.0.0.1:8000/api/validate/1

# Scan for duplicates
curl -X POST http://127.0.0.1:8000/api/duplicates/1

# List duplicate pairs
curl http://127.0.0.1:8000/api/duplicates
```

**`POST /api/duplicates/{batch_id}`** returns a summary split by category:

```json
{
  "batch_id": 1,
  "exact_duplicates": 2,
  "vendor_duplicates": 0,
  "near_duplicates": 1,
  "suspicious_duplicates": 2
}
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** and `pip`
- **Node.js 18+** and `npm`
- **MySQL 8.0** (optional — SQLite is used by default for quick start)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Copy the env template (adjust credentials / database URL as needed)
copy backend\.env.example backend\.env        # Windows
# cp backend/.env.example backend/.env        # macOS/Linux

uvicorn backend.app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for interactive API docs.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — login with `admin` / `admin123`.

### 3. MySQL (optional, production)

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p invoice_db < database/seed_data.sql
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/invoice_db?charset=utf8mb4"
```

No code changes required to switch databases — configuration is fully env-driven.

### 4. Train the ML model (optional)

```bash
python -m ml_engine.train_model --data database/sample_invoices.csv
```

Writes `ml_engine/model.pkl` + `ml_engine/scaler.pkl`. If the artefacts are absent,
`ml_engine/predict.py` falls back to fitting Isolation Forest on the incoming batch.

---

## 🧪 How Risk Scoring Works

1. **Rule engine** (`services/validation_service.py`) enforces hard business rules —
   duplicate ID, GST/amount mismatch, negative amounts, invalid quantity/unit price,
   empty product names, future dates.
2. **ML model** (`ml_engine/`) runs an **Isolation Forest** over amount, quantity,
   unit price and vendor-relative pricing to catch anomalies fixed rules miss
   (e.g. an invoice that's individually *valid* but priced far outside the vendor's
   history).
3. **`risk_service.py`** blends both into a single 0–100 score and final status —
   a GST mismatch or flagged duplicate always forces `High Risk` / `Critical`.

**Invoice statuses:** `Pending` · `Valid` · `Needs Review` · `High Risk` · `Critical` · `Duplicate` · `Paid`

---

## 🧭 Roadmap

- [x] **Phase 1** — FastAPI foundation, config, CORS, health
- [x] **Phase 2** — MySQL schema, models, SQLite-compatible dev DB
- [x] **Phase 3** — Secure CSV/XLSX upload pipeline + audit logging
- [x] **Phase 4** — Rule-based validation engine
- [x] **Phase 5** — Duplicate detection intelligence (5-level match + confidence)
- [ ] **Phase 6** — PDF / OCR invoice ingestion
- [ ] **Phase 7** — Real-time API validation & webhooks
- [ ] **Phase 8** — Vendor fraud detection & payment reconciliation
- [ ] **Phase 9** — ERP integration (SAP / Tally / Zoho)
- [ ] **Phase 10** — Docker Compose deployment + CI/CD pipelines
- [ ] **Phase 11** — Power BI executive dashboard (in `analytics/`)

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Commit your changes
4. Push and open a pull request

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---

<div align="center">

Built with ❤️ using FastAPI, React, MySQL & scikit-learn.

**Report · Review · Pay with confidence.**

</div>
