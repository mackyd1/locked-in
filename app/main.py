from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse

from app.config import get_settings
from app.rate_limit import RateLimitMiddleware
from app.routes import health, jobs, me, stats

settings = get_settings()
DASHBOARD = Path(__file__).resolve().parent / "static" / "dashboard.html"

app = FastAPI(
    title="Locked-In",
    description="Personal stats API with Redis rate limiting and RQ workers.",
    version="0.1.0",
)
app.add_middleware(RateLimitMiddleware)
app.include_router(health.router)
app.include_router(me.router)
app.include_router(stats.router)
app.include_router(jobs.router)


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=307)


@app.get("/dashboard")
async def dashboard() -> FileResponse:
    return FileResponse(DASHBOARD, media_type="text/html")
