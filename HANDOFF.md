# Locked-In — continue here

## Done

- FastAPI app with `/health`, `/v1/me/summary`, `/v1/stats/{domain}`, `/v1/jobs/sync`
- Redis sliding-window rate limit middleware (`429` + `Retry-After`); fails open with `X-RateLimit-Degraded: 1` if Redis is down
- RQ worker + `sync_provider` job
- Providers: LeetCode active; Hevy (`gym`) **on hold** (Pro-only API) — client code kept, not called
- `docker-compose.yml` (api + worker + redis), `scripts/load_test.py`

## Your next steps

1. Set `.env`: strong `API_KEY` (Locked-In auth header), `LEETCODE_USERNAME` — skip `HEVY_API_KEY`
2. `docker compose up -d --force-recreate api worker` after editing `.env`
3. `curl -H "x-api-key: ..." http://127.0.0.1:8000/v1/me/summary`
4. `python scripts/load_test.py --n 50` to show 429s
5. Later: swap gym for a free source, or add Spotify / GitHub / etc.

## Related

- Old TS scaffold (do not continue): `C:\Users\macky\Projects\personal-api`
- Forge v2 (Tree-sitter + hybrid eval): `C:\Users\macky\Projects\forge`
