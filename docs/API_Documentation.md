# API Documentation

> InvoiceGuard-AI v1.0.0 · Full REST reference, formatted like an OpenAPI /
> Swagger document. Interactive live docs are also available at
> **`http://127.0.0.1:8000/docs`** once the server is running.

**Conventions**

- Base URL: `http://127.0.0.1:8000`
- All routes (except `/health`) are prefixed with `/api`.
- Requests and responses are JSON unless stated otherwise (uploads are `multipart/form-data`).
- Errors use the standard FastAPI envelope: `{"detail": "<message>"}`.

---

## Table of Contents

1. [Health](#health)
2. [Auth](#auth)
3. [Uploads](#uploads)
4. [Invoices](#invoices)
5. [Validation](#validation)
6. [Duplicates](#duplicates)
7. [Reports](#reports)
8. [Error Reference](#error-reference)

---

## Health

### `GET /health` · `GET /api/health`

Live uptime / readiness check. **Always returns 200 while the process is alive**;
database state is reported in the body (the API never crash-loops on a missing
database).

**Response `200`**

```json
{
  "status": "running",
  "service": "Invoice Error Detector API",
  "database": "connected",
  "tables": "ready",
  "seed_data": true
}
```

When the database is down, `database` is `"unavailable"` and a `reason` field is
added (never a stack trace):

```json
{
  "status": "running",
  "database": "unavailable",
  "reason": "Database connection failed — check DATABASE_URL and that the server is running."
}
```

**cURL**

```bash
curl http://127.0.0.1:8000/health
```

**Status codes**

| Code | Meaning |
|------|---------|
| 200  | Process alive (DB state is in the payload) |

---

## Auth

### `POST /api/auth/login`

Demo authentication. Exchanges a username/password for a bearer token.

> Production note: this is a **demo** implementation using a fixed credential
> set and an HMAC-signed token (not a real JWT). Swap for OAuth2 + hashed
> passwords in production.

**Request**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response `200`**

```json
{
  "access_token": "admin.1769.....d3f0",
  "token_type": "bearer"
}
```

**cURL**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Error cases**

| Code | Body |
|------|------|
| 401  | `{"detail": "Invalid username or password"}` |

Default credentials are configurable via `DEMO_USER` / `DEMO_PASSWORD` env vars.

---

## Uploads

### `POST /api/upload/single`

Upload a file containing **exactly one invoice**. Rejected (400) if the file
contains more than one invoice — use bulk instead.

### `POST /api/upload/bulk`

Upload a file containing **many invoices** (CSV or XLSX). Processed as a single
**transactional batch**: on any database error the entire upload rolls back and
the batch is marked `Failed`.

**Request** — `multipart/form-data`, field `file`.

Supported: `.csv`, `.xlsx`, max **20 MB**.

**Response `200`**

```json
{
  "batch_id": 4,
  "file_name": "sample_invoices.csv",
  "total": 5,
  "processed": 5,
  "failed": 0,
  "status": "Completed"
}
```

**cURL**

```bash
curl -F "file=@database/sample_invoices.csv" http://127.0.0.1:8000/api/upload/bulk
```

**Error cases**

| Code | Reason |
|------|--------|
| 400  | Unsupported file type (not `.csv`/`.xlsx`) |
| 400  | Disallowed MIME / content type |
| 400  | Empty file |
| 400  | Corrupted / invalid Excel (not an Open XML document, magic-byte check) |
| 400  | Parser or business-rule failure (e.g. single upload with many invoices) |
| 413  | File exceeds the 20 MB upload limit |
| 500  | Database persistence error (`UploadPersistError`) |

Each rejection and each pipeline stage is written to the **audit log**
(`backend/logs/upload_audit.log`) with `batch_id` and details.

---

### `GET /api/upload/history`

List the most recent **50** upload batches, newest first.

**Response `200`** — array of:

```json
[
  {
    "batch_id": 4,
    "file_name": "sample_invoices.csv",
    "uploaded_by": "admin",
    "uploaded_at": "2026-08-29T18:00:00",
    "total_invoices": 5,
    "processed_invoices": 5,
    "failed_invoices": 0,
    "status": "Completed"
  }
]
```

**cURL**

```bash
curl http://127.0.0.1:8000/api/upload/history
```

If the database is unavailable, an empty list is returned (no 500).

---

### `GET /api/upload/{batch_id}`

Return one batch plus its invoices.

**Response `200`**

```json
{
  "batch_id": 4,
  "file_name": "sample_invoices.csv",
  "uploaded_by": "admin",
  "uploaded_at": "2026-08-29T18:00:00",
  "total_invoices": 5,
  "processed_invoices": 5,
  "failed_invoices": 0,
  "status": "Completed",
  "invoices": [
    {
      "invoice_number": "ABC-2026-001",
      "invoice_date": "2026-08-01",
      "vendor_name": "Globex Corp",
      "subtotal": 1000.0,
      "tax_amount": 180.0,
      "total_amount": 1180.0,
      "status": "Valid"
    }
  ]
}
```

**Error cases**

| Code | Body |
|------|------|
| 404  | `{"detail": "Batch {batch_id} not found."}` |

> If the database is unavailable, a well-formed empty `BatchDetail` (status
> `"Processing"`, empty `invoices`) is returned instead of a 500 so the UI
> degrades gracefully.

---

## Invoices

### `GET /api/invoices`

List all invoices, newest invoice-date first.

**Response `200`** — array of:

```json
[
  {
    "invoice_id": 12,
    "invoice_date": "2026-08-01",
    "total_amount": 1180.0,
    "risk_score": 15.0,
    "status": "Valid",
    "vendor_name": "Globex Corp"
  }
]
```

**cURL**

```bash
curl http://127.0.0.1:8000/api/invoices
```

Returns an empty list when the database is unavailable (never a 500).

---

### `GET /api/invoices/{invoice_id}`

Return a single invoice with its line items and vendor.

**Response `200`**

```json
{
  "invoice_id": 12,
  "invoice_date": "2026-08-01",
  "total_amount": 1180.0,
  "risk_score": 15.0,
  "status": "Valid",
  "vendor": {
    "vendor_id": 3,
    "vendor_name": "Globex Corp",
    "gst_number": "27AAACH7409R1Z7"
  },
  "items": [
    {
      "product_name": "Steel Bolts",
      "quantity": 100,
      "unit_price": 10.0
    }
  ]
}
```

**Error cases**

| Code | Body |
|------|------|
| 404  | `{"detail": "Invoice not found"}` |

---

## Validation

### `POST /api/validate/{batch_id}`

Run the **rule-based validation engine** over every invoice in the batch,
persist findings and updated statuses, then return a batch summary.

**Request** — path parameter, no body.

**Response `200`**

```json
{
  "batch_id": 4,
  "total_invoices": 5,
  "valid": 3,
  "needs_review": 1,
  "high_risk": 1,
  "critical": 0,
  "validation_time": "0.42s"
}
```

**cURL**

```bash
curl -X POST http://127.0.0.1:8000/api/validate/4
```

**Error cases**

| Code | Body |
|------|------|
| 404  | `{"detail": "Batch {id} not found."}` |
| 500  | Validation engine error |

---

## Duplicates

### `POST /api/duplicates/{batch_id}`

Run **5-level duplicate detection** for every invoice in the batch — comparing
against all same-company invoices across all batches — persist findings +
confidence scores, apply risk penalties, and return per-level counts.

**Response `200`**

```json
{
  "batch_id": 4,
  "exact_duplicates": 1,
  "vendor_duplicates": 0,
  "near_duplicates": 1,
  "suspicious_duplicates": 0
}
```

**cURL**

```bash
curl -X POST http://127.0.0.1:8000/api/duplicates/4
```

**Error cases**

| Code | Body |
|------|------|
| 404  | `{"detail": "Batch {id} not found."}` |
| 500  | Duplicate-scan engine error |

---

### `GET /api/duplicates`

List all detected duplicate pairs, deduplicated (one row per pair), across all
batches.

**Response `200`** — array of:

```json
[
  {
    "invoice_a_id": 10,
    "invoice_a_number": "ABC-2026-001",
    "invoice_b_id": 42,
    "invoice_b_number": "ABC-2026-001",
    "vendor_name": "Globex Corp",
    "amount_a": 1180.0,
    "amount_b": 1180.0,
    "invoice_date_a": "2026-08-01",
    "invoice_date_b": "2026-06-27",
    "matched_ids": [10, 42],
    "validation_type": "exact",
    "severity": "CRITICAL",
    "confidence_score": 100.0,
    "similarity": 1.0
  }
]
```

**cURL**

```bash
curl http://127.0.0.1:8000/api/duplicates
```

Returns an empty array on an unavailable database (never a 500).

---

## Reports

Reports re-export the **last generated report** (from the previous validation /
upload in the running process). If none exists yet you get a 404.

> In-memory caveat: the report is held in the process. To produce a report,
> upload + validate first (see the workflow in the README).

### `GET /api/report/csv`
### `GET /api/report/excel`
### `GET /api/report/pdf`

**Response**

- `200` — file download (`Content-Disposition: attachment`) of
  `invoice_validation_report.{csv|xlsx|pdf}`.

**cURL**

```bash
curl -OJ http://127.0.0.1:8000/api/report/csv
curl -OJ http://127.0.0.1:8000/api/report/excel
curl -OJ http://127.0.0.1:8000/api/report/pdf
```

**Error cases**

| Code | Body |
|------|------|
| 404  | `{"detail": "No report generated yet — call /api/upload first"}` |

---

## Error Reference

| Status | Meaning | Common triggers |
|--------|---------|-----------------|
| 401 | Unauthorized | Bad demo credentials |
| 404 | Not found | Unknown batch or invoice, no report generated |
| 400 | Bad request | Unsupported file, disallowed MIME, empty/corrupt file, single-upload with many invoices |
| 413 | Payload too large | File over the 20 MB cap |
| 500 | Internal error | DB persistence / validation / duplicate-scan engine failure |

All error bodies use the standard FastAPI shape: `{"detail": "..."}`.

---

© 2026 InvoiceGuard-AI · [Back to README](../README.md)
