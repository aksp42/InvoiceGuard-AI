# InvoiceGuard-AI — Brand Guide

> Sprint 2 · Repository Branding. A modern fintech identity for a financial
> validation product. This document defines the official color palette, logo,
> banner, favicon and usage rules so every asset stays consistent.

---

## Palette

Primary, accent and semantic colors. Use the semantic tones (`success`,
`warning`, `danger`) only for statuses — never for decoration.

| Token              | Hex       | Usage                                            |
|--------------------|-----------|--------------------------------------------------|
| `--primary`        | `#0F172A` | Primary surfaces, dark backgrounds, headings      |
| `--accent`         | `#3B82F6` | Interactive elements, links, primary buttons      |
| `--success`        | `#22C55E` | Valid / completed / positive states               |
| `--warning`        | `#F59E0B` | Needs review / near-duplicate / warnings          |
| `--danger`         | `#EF4444` | Critical / high-risk / errors                     |

### Supporting tones (neutrals)

| Token              | Hex       | Usage                                            |
|--------------------|-----------|--------------------------------------------------|
| `--surface`        | `#F8FAFC` | Page background                                 |
| `--surface-2`      | `#FFFFFF` | Cards, elevated surfaces                        |
| `--text`           | `#0F172A` | Primary text                                    |
| `--text-muted`     | `#64748B` | Secondary / muted text                          |
| `--border`         | `#E2E8F0` | Borders, dividers                               |

---

## Logo

**`docs/assets/brand/logo.svg`** — a shield fused with an invoice page and a
success checkmark. The shield communicates protection; the checkmark conveys
validation passing; the accent dot hints at ML / analytics intelligence.

### Logo usage rules

- Always render on a dark `#0F172A` or white background — never on busy imagery.
- Minimum clear-space: the height of the shield on every side.
- Do not recolor, rotate, add drop shadows, or place the mark on a gradient
  different from the approved brand background.
- Do not stretch or distort. Scale proportionally from the SVG source.

---

## Banner

**`docs/assets/brand/banner.svg`** — the GitHub **social preview** (1280×640).
Upload it in **Repository → Settings → Social preview**. The banner pairs the
mark with the tagline and feature chips on the brand gradient.

---

## Favicon

**`docs/assets/brand/favicon.svg`** — the 32×32 shield mark. Also mirrored in
`frontend/public/` for the browser tab. Export 16×16, 32×32 and 48×48 PNGs as
needed for deployment.

---

## Typography (recommended)

| Role       | Face                   |
|------------|------------------------|
| Headings   | `Inter` 700 / 600      |
| Body       | `Inter` 400            |
| Mono       | `JetBrains Mono`       |

Fallbacks: `Segoe UI`, `Arial`, `system-ui`.

---

## Voice & tone

- Confident, concise, enterprise-grade.
- Lead with outcomes ("catches duplicate submissions before payment").
- Prefer active voice and measurable impact.

---

## File inventory

| Asset                      | Path                        |
|----------------------------|-----------------------------|
| Logo (SVG)                 | `docs/assets/brand/logo.svg`      |
| Banner / social preview    | `docs/assets/brand/banner.svg`    |
| Favicon (SVG)              | `docs/assets/brand/favicon.svg`   |
| Brand guide (this file)    | `docs/BRAND.md`                   |

---

© 2026 InvoiceGuard-AI. MIT License.
