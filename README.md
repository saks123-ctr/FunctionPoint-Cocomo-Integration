# Function Point Calculator + Basic COCOMO Estimator

Full-stack web app: **Django REST Framework** backend, **HTML/CSS/JS** dashboard with **Chart.js**, optional **PostgreSQL** (SQLite fallback for local dev).

## Features

- **Function points**: EI, EO, EQ, ILF, EIF with simple / average / complex counts and standard weights.
- **GSC**: 14 general system characteristics (0–5), **CAF = 0.65 + 0.01 × Σ GSC**, **FP = UFP × CAF**.
- **Basic COCOMO**: Organic, Semi-detached, Embedded modes; **KLOC = FP / 100**.
- **REST API**: `POST /calculate-fp/`, `POST /calculate-cocomo/` (same handlers at `POST /api/calculate-fp/` and `POST /api/calculate-cocomo/`), `GET|POST /api/projects/`, `GET /api/export-pdf/<id>/`, `GET /api/meta/`.
- **PDF reports** (ReportLab): downloadable snapshot for a saved project, with FP/COCOMO summary and timestamp.
- **UI**: Debounced live recalculation, UFP breakdown doughnut, effort vs TDEV bar chart, optional saved projects, **Download report** (last save) and per-row **PDF** in history.

## Layout

- `backend/` — Django project (`config`) and `estimator` app.
- `backend/estimator/services/` — FP/COCOMO logic and `pdf_service` (ReportLab PDF generation).
- `backend/estimator/utils/` — constants, `formatters` (decimals, dates, COCOMO labels).
- `backend/estimator/api/` — DRF serializers and views.
- `frontend/templates/` — dashboard template.
- `frontend/static/` — CSS and JavaScript.

## Setup

### 1. Python environment

```bash
cd "c:\All folders\SE_Project"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables (optional)

Copy `.env.example` to `.env` in the repo root.

- **`DATABASE_URL`**: If set to a PostgreSQL URL (`postgresql://user:pass@host:port/dbname`), Django uses PostgreSQL. If omitted, **SQLite** is used (`backend/db.sqlite3`).
- **`SECRET_KEY`**, **`DEBUG`**, **`ALLOWED_HOSTS`**, **`CORS_ALLOWED_ORIGINS`** (when `DEBUG=False`).

### 3. Database and run

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the dashboard. Admin: `python manage.py createsuperuser` then [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

### 4. Tests

```bash
cd backend
python manage.py test estimator
```

## API examples

**Calculate FP**

`POST /calculate-fp/` (or `POST /api/calculate-fp/`)

```json
{
  "ei": { "simple": 2, "average": 1, "complex": 0 },
  "eo": { "simple": 0, "average": 0, "complex": 0 },
  "eq": { "simple": 0, "average": 0, "complex": 0 },
  "ilf": { "simple": 0, "average": 0, "complex": 0 },
  "eif": { "simple": 0, "average": 0, "complex": 0 },
  "gsc": [3,3,3,3,3,3,3,3,3,3,3,3,3,3]
}
```

**COCOMO**

`POST /calculate-cocomo/` (or `POST /api/calculate-cocomo/`)

```json
{ "fp": 42.5, "mode": "semi_detached" }
```

Modes: `organic`, `semi_detached`, `embedded`.

**Export PDF (saved project)**

`GET /api/export-pdf/<project_id>/`

Returns `application/pdf` with `Content-Disposition: attachment`. Create a snapshot first via `POST /api/projects/`.

## Notes

- Estimation formulas follow the specification you provided (IFPUG-style weights, GSC/CAF, Basic COCOMO, FP→KLOC rule).
- Calculation endpoints use `AllowAny` for easy integration; tighten authentication for production deployments.
