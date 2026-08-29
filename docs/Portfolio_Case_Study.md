# Portfolio Case Study — InvoiceGuard-AI

> **Recruiter-focused write-up.** This document explains the *why* behind a
> production-grade invoice validation platform: the problem, the solution, the
> architecture, the engineering decisions, the performance characteristics and
> the business impact.

---

## TL;DR

| | |
|---|---|
| **What** | A full-stack, AI-assisted invoice validation & duplicate-detection engine |
| **Stack** | React · FastAPI · MySQL · scikit-learn (Isolation Forest) · Power BI |
| **Key win** | Explainable rules + ML anomaly scoring + 5-level duplicate intelligence, wrapped in a production-safe, auditable pipeline |
| **Repo** | [Invoice Guard-AI](https://github.com/) — see `README.md` |

---

## Problem

Accounts-payable teams face a silent, expensive risk: **duplicate and invalid
invoices reaching payment.** Common failure modes:

- The same vendor bill submitted **twice** (exact or near-duplicate).
- **Amount / GST mismatches** and line items that don't add up to the total.
- **Missing fields, future dates, negative values** slipping past manual review.
- **Outlier invoices** that are individually valid yet priced wildly outside a
  vendor's historical range.

The two naive approaches both fail:

- **Pure manual review** does not scale.
- **Pure machine learning** is a black box — finance needs a *reason* for every
  flag, not just a probability.

**The requirement:** a system that is *fast, trustworthy, explainable* and
*production-safe* — from upload to ledger.

---

## Solution

**InvoiceGuard-AI** is a full pipeline:

1. **Secure upload** — CSV/XLSX parsed safely (20 MB streaming cap, MIME +
   extension allow-list, magic-byte sniffing, sanitised filenames), stored in a
   **single atomic transaction** per batch with a complete audit log.
2. **Rule-based validation** — hard business rules emit explicit, machine-readable
   findings (GST/amount mismatch, negative amounts, invalid quantity/unit price,
   missing fields, future dates).
3. **5-level duplicate intelligence** — exact, vendor, near, date-window and
   line-item matching, each with a confidence score, compared against **all**
   historical invoices for the same company.
4. **ML risk blend** — an Isolation-Forest anomaly score is fused with rule
   findings into one actionable 0–100 `risk_score` and final status.
5. **Executive analytics** — a 5-page dashboard, CSV/Excel/PDF exports, and a
   Power BI solution, all over the same relational data.

---

## Architecture

```
 React SPA ──HTTP/JSON──► FastAPI (routes → services → SQLAlchemy ORM) ──► MySQL 8
                              │                                              ▲
                              │ joblib                                       │ SQL
                              ▼                                              │
                    ml_engine/ (Isolation Forest) ◄────—────—────—────—— Power BI / SQL
```

- **Frontend:** React 18 + Vite SPA; a dedicated analytics module loads
  invoices, history and duplicates **in parallel** with graceful error handling.
- **Backend:** FastAPI with separated routers, services and models; 12-factor
  env-driven config; CORS for the dev origin.
- **Database:** MySQL 8 (InnoDB / utf8mb4) in production; SQLite out of the box
  for development — **no code change to switch**.
- **ML:** a joblib-serialised Isolation Forest, with a fallback that fits on the
  incoming batch when artefacts are absent.

See [`docs/System_Architecture.md`](System_Architecture.md) for full Mermaid
diagrams.

---

## Engineering Decisions

### 1. Rule-based validation before ML

**Decision:** enforce deterministic business rules *first*; use ML *only* as a
complementary anomaly signal.

**Why:** Finance teams must defend every decision. Rules give explicit,
reproducible reasons (`code` + `message`) that are audit-ready and easy to
reason about. ML alone can't offer that certainty. Rules handle the 90% that is
well-defined; the Isolation Forest catches the long tail that rules miss.

### 2. Batch-based uploads

**Decision:** each upload creates a batch and persists invoices inside **one
transaction**, using a nested savepoint.

**Why:** a multi-invoice file should never leave the database half-written.
If any invoice fails to persist, the whole batch rolls back and the batch row is
committed as `Failed` — no partial data, and every stage is audit-logged.

### 3. Confidence scores

**Decision:** every duplicate finding carries a `confidence_score` and
`similarity`, and risk penalties are applied **once per pair** (idempotent).

**Why:** it makes re-scans safe (no double-penalising), and gives users a
defensible basis for escalating review severity instead of a binary yes/no.

### 4. Duplicate intelligence (deterministic, not ML)

**Decision:** use RapidFuzz-driven matching across five explicit levels rather
than a learned classifier for the core duplicate check.

**Why:** duplicates are largely a well-defined matching problem (same number,
same vendor+amount+date, near-identical references). Determinism + confidence +
severity gives explainability and testability that a black-box model can't match.

### 5. Production-readiness as a first-class concern

**Decision:** safe DB initialisation, auto-seed on empty DB, read guards that
return empty responses instead of HTTP 500, and an expanded `/health`.

**Why:** a dashboard on an empty or briefly unavailable database should degrade
gracefully — never crash the process or blank the UI.

---

## Challenges

| Challenge | How it was met |
|-----------|----------------|
| Explainable yet powerful detection | Layered rules + ML anomaly + duplicate penalties blended by `risk_service` |
| Transactional integrity for multi-invoice files | Nested savepoint; whole-upload rollback; batch marked `Failed` |
| Duplicate detection across time | Matched against all same-company invoices across all batches |
| Secure arbitrary file intake | Extension/MIME allow-lists, magic-byte sniffing, 20 MB streaming cap, filename sanitisation |
| Empty / unavailable database crashes | `ensure_tables`, auto-create, read guards, `/health` readiness |
| Keeping tests backward-compatible | Auto-seed is opt-out (tests assert pristine DB set `AUTO_SEED=false`) |

---

## Performance & Reliability

- **Production-safe uploads** — one transaction per batch; streamed size cap;
  pre-flight rejections happen before any DB write.
- **Transaction safety** — savepoint isolates invoice/vendor writes so a fatal
  DB error never leaves partial invoices.
- **Audit logging** — `backend/logs/upload_audit.log` records every stage
  (upload started → parsing → save → completed/failed) with `batch_id` and
  details.
- **Graceful degradation** — read endpoints return empty collections on DB
  failure; `/health` reports database/tables/seed state without crashing.
- **Idempotent scans** — re-running validation or duplicate detection never
  double-accumulates penalties.

---

## Impact

- **Duplicates never reach the ledger** — multi-level matching catches both
  exact resubmissions and near-duplicate variations submitted months apart.
- **Every flag is explainable** — rules + confidence scores give finance teams
  defensible reasons to act, reducing false accusations against honest vendors.
- **Faster triage** — a live dashboard surfaces risk exposure, vendor behaviour
  and validation trends in seconds instead of spreadsheet archaeology.
- **Executive visibility** — Power BI + SQL analytics let leadership see risk
  across the whole invoice population.
- **Audit-ready** — a complete upload audit trail supports compliance and
  dispute resolution.

---

## Repository Readiness

- **Documentation:** README, architecture, API reference, demo guide, screenshot
  guide, brand guide, changelog.
- **Community:** CONTRIBUTING, CODE_OF_CONDUCT, issue & PR templates.
- **Deliverables:** full-stack application, SQL schema, seed data, sample files,
  Power BI dashboard, ML engine.

---

© 2026 InvoiceGuard-AI · [Back to README](../README.md)
