# Demo Guide

> A **90-second** live demo script for InvoiceGuard-AI — perfect for interviews,
> portfolio reviews and stakeholder walkthroughs. Every segment has a clear
> message, the exact screen to show, and what to say.

---

## Before You Start

**Prepare the environment (5 minutes):**

1. Start the backend: `uvicorn backend.app.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Open **http://localhost:5173**
4. Ensure sample data is present (`AUTO_SEED=true` seeds a fresh DB) or upload
   `database/sample_invoices.csv` first.
5. Keep a copy of the sample CSV on your desktop for a clean upload clip.
6. Pre-open the pages you'll visit in separate tabs (or navigate quickly).

**Pacing rule:** one message per segment, no more. Pause, let the screen tell
the story.

---

## Demo Script — 90 Seconds

### 0:00 – 0:15 · Problem (15s)

**Screen:** Dashboard (Executive Overview) after the login screen.

> "Finance teams lose real money to duplicate and fraudulent invoices that slip
> past manual review. Every upload is a risk: the same vendor bill sent twice,
> a miscalculated GST amount, a line item that doesn't add up. Manual review
> doesn't scale and pure machine-learning is a black box you can't trust or
> explain."

**Goal:** Name the problem **and** the barrier (explainability).

---

### 0:15 – 0:30 · Upload (15s)

**Screen:** Upload page.

> "InvoiceGuard-AI turns invoice intake into a safe, auditable pipeline. I'll
> upload a batch of invoices — CSV or Excel — and watch the system parse,
> sanitise and store them inside a single atomic transaction. Secure by design:
> a 20-megabyte streaming limit, strict file and MIME checks, and a full audit
> log for every upload."

**Action:** Drag the sample CSV onto the upload box and submit. Pause on the
success summary.

---

### 0:30 – 0:45 · Validation (15s)

**Screen:** Validation summary.

> "Now the rule engine runs over every invoice: it checks GST versus amount,
> negative values, invalid quantities, missing fields and future dates. Each
> rule produces an explicit, machine-readable finding — never a black box. Every
> flagged invoice gets a clear reason and a risk score."

**Action:** Trigger validation on the batch; highlight the per-status counts
(valid vs. needs review vs. high risk).

---

### 0:45 – 1:00 · Duplicate Detection (15s)

**Screen:** Duplicate Detection summary (and/or Duplicate Intelligence page).

> "Next, the five-level duplicate intelligence: exact, vendor, near, date-window
> and line-item matching. It compares new invoices against every historical
> invoice for the same company — so a bill submitted two months apart still gets
> caught. Every finding carries a confidence score, and duplicate risk penalties
> are applied exactly once."

**Action:** Run the duplicate scan; point out the per-level counts and a specific
duplicate pair.

---

### 1:00 – 1:15 · Dashboard & Analytics (15s)

**Screen:** Executive Overview + Vendor Intelligence / Validation Insights.

> "All of that lands on a live executive dashboard — five analytics views:
> overview, vendor intelligence, validation insights, duplicate intelligence and
> an audit center. Finance can see risk exposure, vendor behaviour and issue
> trends at a glance, and export the same data to CSV, Excel, PDF or Power BI."

**Action:** Scroll the KPI cards and one chart; click into Vendor Intelligence.

---

### 1:15 – 1:30 · Closing (15s)

**Screen:** Overall dashboard or audit center.

> "InvoiceGuard-AI is explainable, production-safe and database-ready — built
> with FastAPI, React, MySQL and an Isolation-Forest risk layer, with Power BI
> analytics on top. It's a complete, deployable system: secure uploads, rule and
> ML risk scoring, duplicate intelligence, and enterprise reporting. Report,
> review, and pay with confidence."

---

## Talking Points

Use these to answer follow-up questions.

### Architecture & decisions

- **Why rule-based first?** Hard business rules are deterministic, explainable
  and auditable — finance needs a reason for every flag, not a probability.
- **SQLAlchemy + MySQL in production, SQLite for dev** — a 12-factor,
  env-driven config means zero code changes to switch databases.
- **Transactional uploads** — one atomic transaction per batch; a failure rolls
  back the whole upload, never leaving partial invoices.

### Duplicate Intelligence

- Five confidence levels with **deterministic penalties**, so escalating review
  severity is always justified.
- **Idempotent re-scans** — running duplicate detection twice never double-penalises.

### Risk scoring

- **Rule engine** triages hard violations; **Isolation Forest** finds anomalies
  that rules miss (e.g. an individually-valid invoice priced far outside a
  vendor's history); `risk_service` blends both into one 0–100 score.

### Production readiness

- Missing tables are auto-created; reads degrade to empty responses instead of
  500s; `/health` reports database + tables + seed state and never crashes.
- A complete **audit log** records every upload event.
- Auto-seeding lets a fresh clone start with meaningful data for demos.

---

## Demo Failure Recovery

| Scenario | Recovery |
|----------|----------|
| Database not running | The API still serves `/health`; reads return empty. Restart DB and refresh. |
| Duplicate scan returns 0 | Expected on truly unique data — mention the 5 levels and show the tooling. |
| Reports 404 | A report only exists after an upload+validate in the running process — do that first. |
| Charts look empty | Re-upload `database/sample_invoices.csv` and validate/scan, then refresh the page. |

---

## Suggested Timeline Card (print this)

| Time | Segment | Screen |
|------|---------|--------|
| 0:00–0:15 | Problem | Dashboard / login |
| 0:15–0:30 | Upload | Upload page |
| 0:30–0:45 | Validation | Validation summary |
| 0:45–1:00 | Duplicate detection | Duplicate summary |
| 1:00–1:15 | Dashboard & analytics | Executive Overview |
| 1:15–1:30 | Closing | Audit center / dashboard |

---

© 2026 InvoiceGuard-AI · [Back to README](../README.md)
