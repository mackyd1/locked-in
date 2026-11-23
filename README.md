# Locked-In

Authenticated personal stats API with Redis rate limiting and background workers.

Aggregate provider data (starting with LeetCode) into a single summary card. Built with FastAPI, Redis, RQ, and Docker Compose.

## Features

- **API key auth** — protected routes require `x-api-key`
- **Redis sliding-window rate limiting** — returns `429` with `Retry-After`
- **RQ workers** — async provider sync jobs
- **Provider adapters** — LeetCode live; gym/other domains plug in via the same interface
- **Dashboard** — http://localhost:8000/dashboard to view your summary in the browser
- **Load test** — `scripts/load_test.py` exercises the rate limiter

## Quick start

```bash
cp .env.example .env
# set API_KEY and LEETCODE_USERNAME
docker compose up --build
```

API: http://127.0.0.1:8000  
Dashboard: http://127.0.0.1:8000/dashboard  
Docs: http://127.0.0.1:8000/docs

### Local (without full Compose)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up redis -d
uvicorn app.main:app --reload --port 8000
python -m app.workers.worker
```

## Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | no | Liveness |
| GET | `/dashboard` | no | Browser UI |
| GET | `/v1/me/summary` | `x-api-key` | Aggregated stats card |
| GET | `/v1/stats/{domain}` | `x-api-key` | Single domain (`leetcode`, `gym`, …) |
| POST | `/v1/jobs/sync` | `x-api-key` | Enqueue provider refresh |
| GET | `/v1/jobs/{job_id}` | `x-api-key` | Job status |

```bash
curl -H "x-api-key: $API_KEY" http://127.0.0.1:8000/v1/me/summary
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `API_KEY` | Secret for `x-api-key` auth |
| `LEETCODE_USERNAME` | Public LeetCode handle |
| `REDIS_URL` | Redis connection (default `redis://localhost:6379/0`) |
| `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | Sliding-window limits |
| `HEVY_API_KEY` | Optional gym provider (requires Hevy Pro API access) |

Missing or unavailable providers degrade that slice only — the summary still returns.

## Layout

```
app/
  main.py           FastAPI app + dashboard
  rate_limit.py     Redis sliding-window middleware
  providers/        Domain adapters (LeetCode, …)
  routes/           health, me, stats, jobs
  workers/          RQ sync jobs
scripts/load_test.py
docker-compose.yml  api + worker + redis
```
