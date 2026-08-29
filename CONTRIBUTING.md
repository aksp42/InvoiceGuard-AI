# Contributing to InvoiceGuard-AI

First off — thanks for taking the time to contribute! 🎉

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing. This
guide helps you get started, set up the project locally, and open your first
pull request.

---

## Table of Contents

- [Development Environment](#development-environment)
- [Project Layout](#project-layout)
- [Branching & Commits](#branching--commits)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Opening a Pull Request](#opening-a-pull-request)
- [Issue / PR labels](#issue--pr-labels)

---

## Development Environment

### Prerequisites

- **Python 3.10+**, **Node.js 18+**
- Optional: **MySQL 8.0** (SQLite works out of the box for development)

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd ..

copy backend\.env.example backend\.env   # Windows
# cp backend/.env.example backend/.env   # macOS/Linux

uvicorn backend.app.main:app --reload
```

> The API **auto-creates tables and seeds sample data** on an empty database at
> startup. To disable for a clean-slate test, set `AUTO_SEED=false` in `.env`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and log in with `admin` / `admin123`.

---

## Project Layout

```
invoice-error-detector/
├── frontend/      # React + Vite SPA (components, pages, analytics)
├── backend/app/   # FastAPI (routes, services, models, utils)
├── ml_engine/     # Isolation Forest (train, predict, feature engineering)
├── database/      # MySQL schema + sample data
├── analytics/     # Power BI + SQL queries
└── docs/          # Architecture, API, demos, case study
```

Whether a change is "backend" or "frontend" usually maps directly to the
`backend/` and `frontend/` directories. Keep related changes together.

---

## Branching & Commits

Work on a dedicated branch named after what you're doing.

```bash
git checkout -b feat/your-feature      # new feature
git checkout -b fix/your-bug           # bug fix
git checkout -b docs/your-doc          # documentation
```

Commit message style (Conventional Commits):

```
feat: add price-anomaly detection endpoint
fix: return empty list instead of 500 on history
docs: expand trend-scanning to 36 months
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`.

---

## Code Standards

- **Never rewrite working features or change business logic** unless the change
  is clearly required and backward-compatible.
- Preserve the existing architecture and naming conventions (see existing routes
  and services).
- Comment code where appropriate — explain **why**, not just **what**.
- Keep functions small and single-purpose.
- Do not commit secrets, `.env` files, tokens, or database credentials.
- Use the environment-driven configuration in `backend/app/config.py` rather
  than hard-coding values.

---

## Testing

The project is typically validated with a mix of **service tests** (unit-level)
and **HTTP tests** (through `fastapi.testclient`).

- Ensure the app starts: `uvicorn backend.app.main:app --reload`
- Run the service + HTTP test suites against your changes.
- After frontend changes, verify the production build:

```bash
cd frontend
npm run build
```

Any test that asserts a **pristine empty database** must opt out of auto-seed by
setting `AUTO_SEED=false` before importing the app (see
`docs/Portfolio_Case_Study.md` for the rationale).

---

## Documentation

When you change behaviour visible to users or consumers:

- Update the relevant section(s) in `README.md`.
- Update `docs/API_Documentation.md` when endpoints or response shapes change.
- Update `docs/System_Architecture.md` when the architecture or data flow changes.

---

## Opening a Pull Request

1. Fork the repo and create your branch from `main`.
2. Make your changes, keeping them focused and reviewable.
3. Run the checks above and confirm the build passes.
4. Push and open a PR using the [pull request template](.github/PULL_REQUEST_TEMPLATE.md).
   Link any related issues with `Closes #12`.

Before you submit:

- [ ] Self-review your diff
- [ ] No secrets committed
- [ ] Backend starts cleanly
- [ ] Tests pass
- [ ] Frontend `npm run build` passes (if you touched the frontend)
- [ ] Docs updated if needed

---

## Issue / PR labels

| Label | Purpose |
|-------|---------|
| `bug`          | Reproducible defect |
| `enhancement`  | Feature / improvement |
| `documentation`| Docs change |
| `good first issue` | Small, beginner-friendly task |
| `help wanted`  | Needs a contributor |
| `triage`       | Needs maintainer review |

---

Thanks again for helping make InvoiceGuard-AI better. 🚀
