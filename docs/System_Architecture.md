# System Architecture

> InvoiceGuard-AI v1.0.0 · A fast, explainable invoice validation and duplicate
> detection pipeline with a production-ready React frontend and FastAPI backend.

This document describes the high-level architecture, how the components
communicate, and the end-to-end data flow. Every diagram is rendered with
**[Mermaid](https://mermaid.js.org/)** and renders natively on GitHub.

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Component Communication](#2-component-communication)
3. [Upload Flow](#3-upload-flow)
4. [Validation Flow](#4-validation-flow)
5. [Duplicate Detection Flow](#5-duplicate-detection-flow)
6. [Dashboard Data Flow](#6-dashboard-data-flow)

---

## 1. High-Level Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        A["React + Vite SPA<br/>(:5173)"] 
        C["cURL / API consumer<br/>(:8000)"]
        P["Power BI / SQL<br/>analytics"]
    end

    subgraph API["API Layer — FastAPI (Uvicorn)"]
        R["Routers<br/>auth · upload · invoices<br/>validation · duplicates · reports"]
        S["Services<br/>parser · validation · duplicate_*<br/>risk · report · upload"]
        M["Models (SQLAlchemy ORM)"]
        H["/health · CORS · access log"]
    end

    subgraph ML["ML / Intelligence Layer"]
        E["ml_engine/<br/>Isolation Forest (joblib)"]
    end

    subgraph DB["Data Layer"]
        D[("MySQL 8<br/>invoice_db — InnoDB/utf8mb4")]
        Q["SQL queries<br/>analytics/sql_queries"]
    end

    D1["Seed<br/>database/seed_data.sql"]

    A -->|"HTTP / JSON"| R
    C -->|"HTTP / JSON"| R
    R --> S
    S --> M
    M -->|"SQLAlchemy"| D
    S -.->|"joblib predict"| E
    E -.->|"risk_score"| S
    P -->|"read replica / SQL"| D
    Q -->|"SQL"| D
    D1 -->|"seed"| D
```

### Explanation

- **React SPA** is the primary client. It talks to the FastAPI backend over
  HTTP/JSON and is served by Vite during development (`:5173`).
- **FastAPI** exposes REST routers and orchestrates parsing, validation,
  duplicate detection, risk blending, reporting and auth through its **service**
  layer.
- **SQLAlchemy ORM** maps the models to MySQL (or SQLite for dev). All writes
  are transactional.
- **ml_engine** holds a joblib-serialised **Isolation Forest**. When present it
  supplies an anomaly signal; when absent, `predict.py` falls back to fitting on
  the incoming batch.
- **Power BI / SQL** read the same relational data for executive reporting and
  is kept deliberately read-only.

---

## 2. Component Communication

```mermaid
flowchart LR
    subgraph FE["Frontend (React)"]
        Pages["Pages & Analytics"] 
        ApiClient["services/api.js"]
    end

    subgraph BE["Backend (FastAPI)"]
        Routes["Routers"]
        Services["Services"]
        Dashboard["useAnalyticsData hook<br/>invoices + history + duplicates"]
    end

    subgraph Store["Persistence"]
        DB[("invoice_db")]
        Logs["upload_audit.log"]
    end

    ML["ml_engine"]

    Pages --> ApiClient
    ApiClient -->|"fetch: {listInvoices, uploadHistory, listDuplicates, ...}"| Routes
    Dashboard -->|"Promise.allSettled — parallel"| Routes
    Routes --> Services
    Services -->|"ORM read/write"| DB
    Services -->|"audit events"| Logs
    Services -->|"joblib predict"| ML
    ML -->|"anomaly score"| Services
```

### Explanation

- The frontend routes **all** requests through one module — `frontend/src/services/api.js`
  — providing a single seam for request/response handling.
- The analytics dashboard loads invoices, upload history and duplicate pairs in
  **parallel** via `Promise.allSettled`, so one failing endpoint degrades
  gracefully instead of blanking the page.
- The backend writes to the database through the ORM and appends human-readable
  **audit events** to `backend/logs/upload_audit.log` on every upload.
- The ML engine is called **indirectly** by the risk service; its artefacts are
  optional at runtime.

---

## 3. Upload Flow

```mermaid
sequenceDiagram
    participant C as Client<br/>(React / cURL)
    participant R as Router<br/>POST /api/upload/*
    participant U as upload_service
    participant P as parser_service
    participant A as Audit log
    participant D as Database (transaction)

    C->>R: file (CSV / XLSX) via multipart
    R->>U: sanitize filename
    R->>U: stream read ≤ 20 MB; check ext + MIME (+zip magic for xlsx)
    U->>D: create batch row (status=Processing) [flush]
    U->>A: "Upload Started" / "Parsing Started"
    U->>P: parse file → standardised rows
    P-->>U: rows
    U->>A: "Parsing Completed"
    U->>D: begin_nested() savepoint
    U->>D: ensure company + vendors + invoices + items
    alt any DB error
        U->>D: roll back savepoint (NO partial invoices)
        U->>D: commit batch as Failed
        U->>A: "Upload Failed"
        U-->>R: HTTP 500 (UploadPersistError)
    else success
        U->>D: commit (batch = Completed)
        U->>A: "Save Completed" / "Upload Completed"
        U-->>R: UploadSummary {batch_id, total, processed, failed}
        R-->>C: 200 JSON
    end
```

### Explanation

- Pre-flight checks (extension, MIME, size, magic bytes) happen **before** any
  batch row is created — invalid payloads never touch the database.
- Each upload persists in **one transaction**. Invoice/vendor writes run in a
  nested **savepoint** so a fatal DB error rolls back the entire upload (no
  partial invoices), after which the batch row is committed as `Failed`.
- Every stage produces an audit event for a full, replayable trail.

---

## 4. Validation Flow

```mermaid
flowchart TD
    S["POST /api/validate/{batch_id}"] --> B["Load batch invoices"]
    B --> IF{"Batch exists?"}
    IF -- No --> 404["HTTP 404 — Batch{id} not found"]
    IF -- Yes --> LOOP["For each invoice"]
    LOOP --> R1["Rule: GST / amount mismatch"]
    LOOP --> R2["Rule: negative amounts"]
    LOOP --> R3["Rule: invalid qty / unit price"]
    LOOP --> R4["Rule: empty / missing fields"]
    LOOP --> R5["Rule: future / missing date"]
    R1 & R2 & R3 & R4 & R5 --> RES["Collect findings [{code, message}]"]
    RES --> ML["Isolation Forest anomaly score"]
    ML --> RISK["risk_service: blend rules + ML + dup penalties<br/>→ risk_score (0-100) + status"]
    RISK --> PERSIST["Persist validation_results + status"]
    PERSIST --> NEXT{"More invoices?"}
    NEXT -- Yes --> LOOP
    NEXT -- No --> SUM["BatchValidationSummary<br/>{valid, needs_review, high_risk, critical}"]
    SUM --> RESP["HTTP 200 JSON"]
    PERSIST --> AUDIT["validation audit log"]
```

### Explanation

- Validation is **rule-first**: five hard business rules produce explicit,
  machine-readable findings (`code` + `message`) — fully auditable.
- Rules are complemented by an **ML anomaly signal** so an individually *valid*
  invoice priced far outside a vendor's history still escalates.
- `risk_service.py` merges the two into one number and status and writes the
  result back so the dashboard and reports reflect it immediately.

---

## 5. Duplicate Detection Flow

```mermaid
flowchart TD
    S["POST /api/duplicates/{batch_id}"] --> LOAD["Load batch invoices +<br/>all same-company invoices (all batches)"]
    LOAD --> PAIRS["Compare invoice pairs"]
    PAIRS --> L1["L1 Exact<br/>identical invoice number<br/>Confidence 100% · +50"]
    PAIRS --> L2["L2 Vendor<br/>same vendor+amount+date<br/>Confidence 98% · +40"]
    PAIRS --> L3["L3 Near<br/>number sim ≥90% + amount ≤₹1<br/>Confidence 95% · +30"]
    PAIRS --> L4["L4 Date<br/>same vendor+amount within 3 days<br/>Confidence 85% · +15"]
    PAIRS --> L5["L5 Item<br/>identical line-item multiset<br/>Confidence 92% · +25"]
    L1 & L2 & L3 & L4 & L5 --> PERSIST["Persist findings + confidence_score"]
    PERSIST --> PEN["Apply risk penalty ONCE per pair (idempotent)"]
    PEN --> CLAMP["Clamp risk_score to 0-100"]
    CLAMP --> SUM["DuplicateSummary<br/>{exact, vendor, near, suspicious}"]
    SUM --> RESP["HTTP 200 JSON"]
    PERSIST --> GET["GET /api/duplicates →<br/>deduplicated pair rows"]
```

### Explanation

- Detection compares each batch invoice against **every same-company invoice
  across all batches**, catching duplicates submitted months apart.
- Five confidence levels range from **exact** (100%) to **line-item** (92%),
  each with a deterministic penalty so the impact is explainable.
- Penalties are applied **once per pair**, so re-scanning is idempotent and risk
  is clamped to 100.

---

## 6. Dashboard Data Flow

```mermaid
flowchart LR
    subgraph FE2["React — analytics (5 pages)"]
        H["useAnalyticsData hook"]
        O["Executive Overview"]
        V["Vendor Intelligence"]
        N["Validation Insights"]
        D["Duplicate Intelligence"]
        A["Audit Center"]
        B["ErrorBanner + retry"]
    end

    subgraph BE2["FastAPI endpoints"]
        EI["GET /api/invoices"]
        EH["GET /api/upload/history"]
        ED["GET /api/duplicates"]
    end

    subgraph DB2["Database"]
        INV[(invoices)]
        BAT[(upload_batch)]
        DUP[(validation_results / pairs)]
    end

    H -->|"Promise.allSettled (parallel)"| EI
    H -->|"Promise.allSettled (parallel)"| EH
    H -->|"Promise.allSettled (parallel)"| ED
    EI --> INV
    EH --> BAT
    ED --> DUP
    EI --> O & V & N
    EH --> O
    ED --> D & A
    H --> B
    B -->|"reload() retry"| H
    O & V & N & D & A -->|"analytics/components/charts + AnimatedCounter"| H

    style O fill:#0F172A,color:#fff
    style V fill:#0F172A,color:#fff
    style N fill:#0F172A,color:#fff
    style D fill:#0F172A,color:#fff
    style A fill:#0F172A,color:#fff
```

### Explanation

- All five analytics pages share a single data hook, `useAnalyticsData`, which
  loads invoices, upload history and duplicate pairs **in parallel**.
- Data is consumed by the same three read endpoints used across the app — no
  dedicated dashboard API is needed, keeping the surface small and consistent.
- `Promise.allSettled` means a single endpoint failure does not blank the page;
  the `ErrorBanner` surfaces the specific error and offers a **Retry** that calls
  `reload()`.

---

© 2026 InvoiceGuard-AI · [Back to README](../README.md)
