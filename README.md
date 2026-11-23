# Locked-In

Personal “locked-in” stats API — gym (Hevy), LeetCode, and room to grow — with production-shaped plumbing: **FastAPI**, **Redis sliding-window rate limits**, and **RQ workers**.

## Why this exists

Two resume stories in one repo:

1. **Systems:** authenticated HTTP API, Redis rate limiting (`429` + `Retry-After`), background sync jobs, load-test script
2. **Product:** a single `/v1/me/summary` card of your training + problem-solving streak (add more providers later)

## Quick start

```powershell
cd C:\Users\macky\Projects\locked-in
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit .env — set API_KEY (your Locked-In auth) + LEETCODE_USERNAME
# HEVY_API_KEY is on hold (Hevy API is Pro-only)
```


Start Redis (Docker):

```powershell
docker compose up redis -d
```

API + worker (two terminals):

```powershell
uvicorn app.main:app --reload --port 8000
python -m app.workers.worker
```

Or everything in compose:

```powershell
docker compose up --build
```

## Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | no | Liveness |
| GET | `/v1/me/summary` | `x-api-key` | Aggregated locked-in card |
| GET | `/v1/stats/{domain}` | `x-api-key` | `gym` or `leetcode` |
| POST | `/v1/jobs/sync` | `x-api-key` | Enqueue provider refresh (`{"domain":"gym"}`) |
| GET | `/v1/jobs/{job_id}` | `x-api-key` | Job status |

```powershell
curl -H "x-api-key: dev-secret-change-me" http://127.0.0.1:8000/v1/me/summary
```

## Rate limiting

Redis sliding window (`RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`). Exceeding the window returns **429** with `Retry-After`.

```powershell
python scripts/load_test.py --n 50
```

## Providers (MVP)

| Domain | Source | Status |
| --- | --- | --- |
| `leetcode` | Public GraphQL (`LEETCODE_USERNAME`) | Active |
| `gym` | Hevy API | **On hold** — Pro subscription required; client kept but not called |

Unavailable domains degrade **that slice only** — the summary still returns.

### `API_KEY` vs provider keys

- **`API_KEY`** — password for *this* Locked-In server. Callers send `x-api-key: <API_KEY>`. Change it from the default.
- **`LEETCODE_USERNAME`** — your public LeetCode handle (no secret).
- **`HEVY_API_KEY`** — unused while gym is on hold.

### Later (not built yet)

Alternate gym source (manual CSV / Strong / another app), Spotify, Letterboxd, reading, GitHub contribution heat — same `Provider` interface in `app/providers/`.

## Layout

```
app/
  main.py              FastAPI app + middleware
  rate_limit.py        Redis sliding-window limiter
  providers/           Hevy + LeetCode adapters
  routes/              health, me, stats, jobs
  workers/             RQ sync_provider job
scripts/load_test.py
docker-compose.yml     api + worker + redis
```

## Resume bullet (after real data)

> Built **Locked-In**, a FastAPI personal stats API with Redis sliding-window rate limiting, RQ background sync workers, and Hevy + LeetCode provider adapters behind an authenticated `/v1/me/summary` endpoint.
