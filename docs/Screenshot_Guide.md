# Screenshot Guide

> Production-quality product screenshots for the README, GitHub social preview
> and portfolio. This guide defines the capture plan, ideal browser size and a
> consistent naming convention so every image looks like it came from the same
> product.

> **Status note:** The initial `screenshots/` folder contains legacy captures
> (dashboard, upload, high_risk, invoice_details, reports). This guide adds the
> full capture plan — including the newer analytics pages — and the naming
> convention to follow when regenerating them.

---

## Ideal Browser Window

Use a **fixed desktop viewport** for consistent, croppable captures:

| Setting | Value |
|---------|-------|
| Browser | Google Chrome (or Chromium-based, e.g. Edge) |
| Window size | **1440 × 900** |
| Zoom | 100% |
| Device toolbar | Off |
| Theme | Match product (light surfaces: `#F8FAFC`) |
| Retina / DPR | 2× for crisp images |

> Capture on a **dark-free, distraction-free** desktop. Hide bookmarks bar;
> use a neutral tab favicon. Avoid showing personal data, bookmarks, OS
> version or multiple tabs.

---

## Naming Convention

One lowercase noun phrase, `kebab-case`, with a `.png` extension.

```
<feature>-<context>.png
```

Examples:

```
dashboard-overview.png
upload-single-invoice.png
validation-batch-summary.png
duplicate-detection-summary.png
vendor-intelligence.png
audit-center-upload-log.png
```

Keep names to **2–3 segments** and re-use the exact feature names so README
links stay stable. Each new navigation item gets its own file.

---

## Capture Checklist

Check every box for a complete, release-ready gallery.

### 1. Login

- [ ] `login.png`
- [ ] Shows the login card centred on the brand surface
- [ ] Credentials prefilled or cleanly blurred (never show real passwords)

### 2. Upload

- [ ] `upload.png` / `upload-single-invoice.png`
- [ ] Upload box visible with the sample file (`database/sample_invoices.csv`)
- [ ] Shows accepted formats (CSV / XLSX) + size limit hint

### 3. Processing

- [ ] `upload-processing.png`
- [ ] Capture a batch mid-processing (status `Processing`) or the success toast
- [ ] Show the returned `UploadSummary` (batch id, totals) if the UI surfaces it

### 4. Validation

- [ ] `validation-batch-summary.png`
- [ ] The validation summary card (valid / needs review / high risk / critical counts)
- [ ] Optionally the per-invoice issues list with rule codes

### 5. Duplicate Detection

- [ ] `duplicate-detection-summary.png`
- [ ] The 5-level duplicate counts (exact / vendor / near / suspicious)
- [ ] **Duplicate Intelligence** analytics page if capturing analytics flows

### 6. Dashboard

- [ ] `dashboard-overview.png`
- [ ] Executive Overview with KPI cards (invoices, total flagged amount, status split)
- [ ] Charts legible and labelled

### 7. Vendor Analytics

- [ ] `vendor-intelligence.png`
- [ ] Vendor table / chart with risk & amount breakdown
- [ ] Sorting or highlighting visible

### 8. Validation Insights / Audit Center

- [ ] `validation-insights.png`
- [ ] `audit-center.png`
- [ ] Validation Insights: issues / rules breakdown chart
- [ ] Audit Center: the upload audit feed (timeline of events)

### 9. Building presentation ratings

- [ ] Executive Overview chart area is not empty (populated or seeded data)
- [ ] All images are `.png`, under ~500 KB each
- [ ] Filenames match the convention above
- [ ] README `screenshots/` references point to real files (no broken links)

---

## Recommended Folder

Keep product screenshots in `screenshots/` at the repo root:

```
screenshots/
├── dashboard-overview.png
├── upload-single-invoice.png
├── validation-batch-summary.png
├── duplicate-detection-summary.png
├── vendor-intelligence.png
├── validation-insights.png
└── audit-center.png
```

Analytics-page captures can also live under `docs/assets/screenshots/` if you
prefer to keep them next to the docs that reference them.

---

## Tips for Crisp, Enterprise-Grade Images

1. **Fill the viewport** — avoid letterboxing; the UI should fill 1440×900.
2. **Use seeded data** so charts and tables are populated (start the API with
   `AUTO_SEED=true` on a fresh DB, or upload `database/sample_invoices.csv`).
3. **Show the value** — captures should tell a story: a batch uploaded, then
   validated, then scanned, then visible on the dashboard.
4. **Keep it clean** — no cursor, no selection highlights, no devtools.
5. **Compress** — PNG for UI; keep the dashboard hero image < 1 MB.

---

## Verifying the Gallery

Before release, confirm every image referenced by the README exists:

```bash
# from the repo root — should list only existing files (no broken links)
Get-Content README.md | Select-String -Pattern '\.\.?/screenshots/[A-Za-z0-9_\-./]+\.png'
```

---

© 2026 InvoiceGuard-AI · [Back to README](../README.md)
