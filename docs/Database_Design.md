# Invoice Error Detector — Database Design

MySQL 8.0  ·  InnoDB  ·  utf8mb4 / utf8mb4_unicode_ci
Source of truth: [`database/schema.sql`](../database/schema.sql)

---

## ER Diagram

```mermaid
erDiagram
    COMPANIES ||--o{ VENDORS : "1 pays many suppliers"
    COMPANIES ||--o{ INVOICES : "receives"
    VENDORS   ||--o{ INVOICES : "issues"
    UPLOAD_BATCHES ||--o{ INVOICES : "loads"
    INVOICES  ||--o{ INVOICE_ITEMS : "contains"
    INVOICES  ||--o{ VALIDATION_RESULTS : "flagged by"

    COMPANIES {
        int company_id PK
        varchar(255) company_name
        char(15) gst_number UK
        varchar(255) email UK
        timestamp created_at
        timestamp updated_at
    }

    VENDORS {
        int vendor_id PK
        int company_id FK
        varchar(255) vendor_name
        char(15) gst_number UK
        varchar(255) email
        varchar(20) phone
        enum status
        timestamp created_at
        timestamp updated_at
    }

    UPLOAD_BATCHES {
        int batch_id PK
        varchar(255) file_name
        varchar(64) uploaded_by
        datetime uploaded_at
        int total_invoices
        int processed_invoices
        int failed_invoices
        enum status
        timestamp created_at
        timestamp updated_at
    }

    INVOICES {
        int invoice_id PK
        int company_id FK
        int vendor_id FK
        varchar(64) invoice_number
        int batch_id FK
        date invoice_date
        decimal(14,2) subtotal
        decimal(14,2) tax_amount
        decimal(14,2) total_amount
        enum status
        decimal(5,2) risk_score
        timestamp created_at
        timestamp updated_at
    }

    INVOICE_ITEMS {
        int item_id PK
        int invoice_id FK
        varchar(255) product_name
        decimal(12,3) quantity
        decimal(14,2) unit_price
        decimal(5,2) tax_percent
        decimal(14,2) line_total
    }

    VALIDATION_RESULTS {
        int validation_id PK
        int invoice_id FK
        varchar(50) validation_type
        enum severity
        varchar(500) message
        decimal(5,2) confidence_score
        timestamp created_at
    }
```

---

## Table Dictionary

### `companies` — the tenant that pays invoices
| Column        | Type            | Notes |
|---------------|-----------------|-------|
| company_id    | INT PK          | Auto increment |
| company_name  | VARCHAR(255)    | NOT NULL |
| gst_number    | CHAR(15) UNIQUE | 15-char GSTIN, validated by `CHECK … REGEXP` |
| email         | VARCHAR(255) UNIQUE | NOT NULL |
| created_at / updated_at | TIMESTAMP | Default now / on-update |

Every financial record belongs to a company. Kept as a separate table so the
design can scale to multiple companies later (multi-tenant).

### `vendors` — suppliers the company procures from
| Column      | Type | Notes |
|-------------|------|-------|
| vendor_id   | INT PK | |
| company_id  | INT FK → companies | CASCADE delete |
| vendor_name | VARCHAR(255) | NOT NULL |
| gst_number  | CHAR(15), UNIQUE (company_id, gst_number) | NULL allowed (foreign/unregistered); repeat NULLs pass the unique index |
| email / phone | VARCHAR | soft email format `CHECK` |
| status      | ENUM(Active, Inactive, Blacklisted) | supports vendor-fraud flagging |

### `invoices` — header record per vendor invoice
| Column         | Type | Notes |
|----------------|------|-------|
| invoice_id     | INT PK | surrogate key |
| company_id / vendor_id | INT FK | CASCADE |
| invoice_number | VARCHAR(64) | vendor's reference **indexed for duplicate lookup** — `idx_invoices_number (invoice_number, company_id)` for number-first, `idx_company_invoice (company_id, invoice_number)` for company-first. Deliberately **not UNIQUE** so duplicate submissions can be stored and flagged. |
| batch_id       | INT FK → upload_batches | nullable; the upload batch that created the invoice (`ON DELETE SET NULL`). Indexed via `idx_invoices_batch`. |
| invoice_date   | DATE | indexed |
| subtotal / tax_amount / total_amount | DECIMAL(14,2) | `CHECK subtotal+tax = total (≤ ₹0.01 tolerance)` |
| status         | ENUM(Pending, Valid, Needs Review, High Risk, Critical, Duplicate, Paid) | lifecycle (`Critical` added in Phase 4) |
| risk_score     | DECIMAL(5,2) | `CHECK 0–100`; indexed for "high risk" scans |
| created_at / updated_at | TIMESTAMP | |

### `upload_batches` — audit log for bulk file upload jobs
| Column             | Type | Notes |
|--------------------|------|-------|
| batch_id           | INT PK | |
| file_name          | VARCHAR(255) | original uploaded file |
| uploaded_by        | VARCHAR(64) | who submitted the file |
| uploaded_at        | DATETIME | when the upload started |
| total_invoices     | INT | rows found in the file |
| processed_invoices | INT | rows successfully stored |
| failed_invoices    | INT | rows rejected by validation |
| status             | ENUM(Processing, Completed, Failed) | job lifecycle; indexed by status + uploader/time |
| created_at / updated_at | TIMESTAMP | |

Each successful invoice links back to its batch via `invoices.batch_id`
(`upload_batches 1 ── N invoices`), enabling later "status of my upload",
re-upload, and per-file failure dashboards.

### `invoice_items` — line-level detail
| Column       | Type | Notes |
|--------------|------|-------|
| item_id      | INT PK | |
| invoice_id   | INT FK → invoices | CASCADE delete; indexed |
| product_name | VARCHAR(255) | indexed for "top products" queries |
| quantity     | DECIMAL(12,3) | supports fractional units |
| unit_price   | DECIMAL(14,2) | |
| tax_percent  | DECIMAL(5,2) | `CHECK 0–100` |
| line_total   | DECIMAL(14,2) | qty × price × (1 + tax%), stored for fast reporting |

### `validation_results` — audit trail of every check flag
| Column           | Type | Notes |
|------------------|------|-------|
| validation_id    | INT PK | |
| invoice_id       | INT FK → invoices | CASCADE; indexed |
| validation_type  | VARCHAR(50) | `CHECK` against known set (DUPLICATE, TOTAL_MISMATCH, GST_MISMATCH, MISSING_FIELD, PRICE_OUTLIER, FUTURE_DATE, INVALID_DATE, RISK_ANOMALY, RECONCILIATION, NEGATIVE_AMOUNT, QUANTITY_INVALID, UNIT_PRICE_INVALID, GST_OUT_OF_RANGE, EMPTY_PRODUCT_NAME, DUPLICATE_EXACT, DUPLICATE_VENDOR, DUPLICATE_NEAR, DUPLICATE_DATE, DUPLICATE_ITEM) |
| severity         | ENUM(INFO, WARNING, ERROR, CRITICAL) | |
| message          | VARCHAR(500) | human-readable detail |
| confidence_score | DECIMAL(5,2) default NULL | ML model confidence (0–100) for the flag; NULL when rule-based. Drives thresholding/filtering in dashboards. |
| created_at       | TIMESTAMP | |

---

## Business rules enforced in the schema

| Rule | Enforcement |
|------|-------------|
| GSTIN format (company/vendor) | `CHECK … REGEXP` on 15-char pattern |
| No negative money | `CHECK` on all amount columns |
| Invoice totals add up | `CHECK ABS((subtotal + tax) − total) ≤ 0.01` |
| Risk score bound | `CHECK risk_score BETWEEN 0 AND 100` |
| No duplicate GSTIN under one company | `UNIQUE (company_id, gst_number)` |
| No duplicate company email | `UNIQUE` |
| Integrity on deletes | `FOREIGN KEY … ON DELETE CASCADE` (items & validation records) |
| Deleting an upload batch never deletes invoices | `invoices.batch_id … ON DELETE SET NULL` |
| Upload batch counters never negative / inconsistent | `CHECK ≥ 0` on `total/processed/failed_invoices` |

---

## How future features map to this design

| Future feature | How the schema supports it |
|----------------|----------------------------|
| Duplicate detection | `idx_company_invoice (company_id, invoice_number)` for company-scoped lookups + `idx_invoices_number` for number-first scans; Phase 5 flags via `validation_results` with `DUPLICATE_EXACT`, `DUPLICATE_VENDOR`, `DUPLICATE_NEAR`, `DUPLICATE_DATE`, `DUPLICATE_ITEM` and writes the deterministic confidence into `confidence_score` |
| Tax / GST validation | recompute in app from `invoice_items` (qty, unit_price, tax_percent) and compare with `invoices.tax_amount` |
| Price-anomaly detection | `invoice_items` history per vendor (unit_price, line_total) for vendor-relative analysis |
| Risk scoring | `invoices.risk_score` (0–100) persisted; `validation_results` holds the reasons |
| Confidence-aware filtering | `validation_results.confidence_score` lets the API/dashboard sort or threshold flags (e.g. "only DUPLICATE with ≥ 95 confidence") and auto-promote/auto-review rules |
| Bulk upload / job tracking | `upload_batches` 1:N with `invoices.batch_id` — per-file status, progress counts, failure counts, re-upload |
| Payment reconciliation | `invoices.status = 'Paid'` + `validation_results('RECONCILIATION')` |

---

## Seed data snapshot (`database/seed_data.sql`)

| Object | Count |
|--------|-------|
| Companies | 1 |
| Vendors   | 5 (1 Blacklisted) |
| Invoices  | 20 — statuses: Paid 4, Valid 3, Pending 3, Needs Review 3, Duplicate 2, High Risk 5 |
| Invoice items | 61 |
| Validation records | 16 — each with a `confidence_score` (DUPLICATE 99.20, GST_MISMATCH 94.80, PRICE_OUTLIER 88.50, TOTAL_MISMATCH 97.40, etc.) |
| Upload batches | 3 — Completed (12 invoices), Failed (2 stored), Processing (3 stored); invoices 18–20 predate batch tracking (`batch_id` NULL) |

Every seeded invoice satisfies `subtotal + tax = total`, verified by the
generator that produced the file. Validation flags cover 10 of the 20
invoices: 2 Duplicate, 5 High Risk (TOTAL_MISMATCH, FUTURE_DATE,
MISSING_FIELD, RISK_ANOMALY ×2), and 3 Needs Review (PRICE_OUTLIER ×2,
GST_MISMATCH), plus RECONCILIATION info records on paid invoices.