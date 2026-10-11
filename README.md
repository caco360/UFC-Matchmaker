# UFC Matchmaking Deployment Notes

## Local development

### Python services

- Put local Python env vars in the repo-root `.env`
- Required for backend and matchup loader:

```env
DATABASE_URL=your_neon_or_local_postgres_url
```

- Optional local override for frontend origins:

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend

- Put local frontend env vars in `app/.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Vercel deployment

Deploy this repo as two separate Vercel projects.

### 1. Backend project

- Root directory: `backend/`
- Entrypoint: `main.py`
- Required env vars:

```env
DATABASE_URL=your_neon_production_url
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

Use a comma-separated value for `CORS_ORIGINS` if you need multiple frontend domains.

### 2. Frontend project

- Root directory: `app/`
- Required env vars:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.vercel.app
```

## Deployment order

1. Deploy the backend Vercel project first
2. Copy the backend deployment URL
3. Set `NEXT_PUBLIC_API_BASE_URL` in the frontend Vercel project
4. Deploy the frontend Vercel project

## Pipeline

The pipeline runs locally on SQLite (`data/ufc.sqlite`, gitignored):

```powershell
py pipeline.py            # scrape (incremental) -> score -> matchmake
py pipeline.py --publish  # same, then load matchups into Postgres/Neon
```

Scraping loads ufcstats pages through headless Chromium (Playwright), because the site now runs a JavaScript browser check. One-time setup:

```powershell
py -m pip install -r requirements.txt
py -m playwright install chromium
```

Single stages can be run from the repo root, e.g. `py -m scoring.src.score_generator`. Tests: `py -m pytest`.
