# Invoice Error Detector — AI-Powered Financial Validation System

An AI-powered system that validates invoices before payment: catches duplicate
submissions, wrong totals, GST mismatches, missing fields, and unusual pricing —
then layers a machine-learning risk score on top using Isolation Forest.

## Project structure

```
invoice-error-detector/
├── README.md
├── LICENSE
├── .gitignore
├── docker-compose.yml          # (Future) containerised stack
│
├── frontend/                   # React + Vite single-page app
│   ├── src/
│   │   ├── components/         # Navbar, Sidebar, KPI_Card, InvoiceTable, UploadBox, RiskBadge
│   │   ├── pages/              # Login, Dashboard, UploadInvoices, InvoiceDetails, HighRisk, Reports, Settings
│   │   ├── services/api.js     # API client
│   │   ├── App.jsx             # Routes
│   │   └── main.jsx
│   └── package.json
│
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── main.py             # App entry point (uvicorn backend.app.main:app)
│   │   ├── config.py           # Env-driven settings
│   │   ├── database.py         # SQLAlchemy engine/session (SQLite default, MySQL-ready)
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── routes/             # upload, invoices, reports, auth
│   │   ├── services/           # validation, duplicate, tax, risk, report services
│   │   ├── models/             # Vendor, Invoice, InvoiceItem
│   │   └── utils/              # csv_reader, excel_reader, pdf_export
│   ├── requirements.txt
│   └── .env                    # copy template below
│
├── ml_engine/                  # AI validation (Isolation Forest)
│   ├── feature_engineering.py
│   ├── anomaly_detection.py
│   ├── train_model.py          # builds model.pkl + scaler.pkl
│   ├── predict.py              # scoring entry point used by the backend
│   ├── model.pkl
│   └── scaler.pkl
│
├── database/
│   ├── schema.sql              # MySQL schema
│   ├── seed_data.sql           # vendors + sample invoices
│   ├── sample_invoices.csv
│   └── sample_bulk_upload.xlsx
│
├── analytics/
│   ├── powerbi/                # Invoice_Dashboard.pbix (placeholder) + Dashboard_Guide.pdf
│   └── sql_queries/            # duplicate_invoices, vendor_analysis, high_risk, monthly_trends
│
├── reports/                    # sample_validation_report.pdf, sample_error_report.xlsx,
│                               # sample_high_risk_report.csv
├── screenshots/                # dashboard/upload/details/high-risk/reports (placeholders)
└── docs/
    ├── Project_Report.docx
    ├── API_Documentation.md
    ├── Database_Design.pdf
    ├── Workflow_Diagram.png
    └── ER_Diagram.png
```

## Setup

Backend:

```bash
cd backend
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger docs.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** (login: `admin` / `admin123`).

## Try it (API)

```bash
curl -F "file=@database/sample_invoices.csv" http://127.0.0.1:8000/api/upload
```

This returns a full validation report per invoice: status (`Valid` /
`Needs Review` / `High Risk` / `Duplicate`), a 0–100 risk score, and the
specific issues found (e.g. "expected ₹1,770.00, got ₹1,200.00").

Download reports:
```bash
curl http://127.0.0.1:8000/api/report/csv   -o report.csv
curl http://127.0.0.1:8000/api/report/excel -o report.xlsx
curl http://127.0.0.1:8000/api/report/pdf   -o report.pdf
```

## ML training

```bash
python -m ml_engine.train_model --data database/sample_invoices.csv
```

Writes `ml_engine/model.pkl` + `ml_engine/scaler.pkl`. If the artefacts are
absent, `ml_engine/predict.py` falls back to fitting on the incoming batch.

## How risk scoring works

1. **Rule engine** (`backend/app/services/validation_service.py`) checks each
   invoice against hard business rules: duplicate ID, total/GST mismatch,
   missing fields, price outliers, future dates.
2. **ML model** (`ml_engine/`) runs an Isolation Forest over invoice amount,
   quantity, unit price, and vendor-relative pricing to catch anomalies fixed
   rules miss — e.g. an invoice that's individually "valid" but priced very
   differently from that vendor's history.
3. **`backend/app/services/risk_service.py`** blends both into one 0–100 risk
   score and final status. A total/GST mismatch or a flagged duplicate always
   forces `High Risk` / `Duplicate`.

## Swapping in MySQL

```bash
export DATABASE_URL="mysql+pymysql://user:password@localhost/invoice_db"
```

Apply the schema and seed: `mysql -u root -p < database/schema.sql
< database/seed_data.sql`. No code changes needed.

## Docker (Future)

`docker-compose.yml` is a placeholder for a containerised deployment:
web (React), api (FastAPI + uvicorn), db (MySQL), and optionally a Power BI
gateway image.

## Next steps / future scope

See `docs/Project_Report.docx` for the roadmap: PDF invoice OCR, real-time API
validation, vendor fraud detection, ERP integration, and a Power BI executive
dashboard on top of this data.