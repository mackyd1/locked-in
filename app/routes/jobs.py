from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from redis import Redis
from rq import Queue

from app.auth import require_api_key
from app.config import get_settings
from app.workers.tasks import sync_provider

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


class SyncJobRequest(BaseModel):
    domain: str = Field(description="Provider domain to sync, e.g. gym or leetcode")


@router.post("/sync")
async def enqueue_sync(body: SyncJobRequest, _: str = Depends(require_api_key)) -> dict:
    if body.domain not in {"gym", "leetcode"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="domain must be gym or leetcode",
        )
    settings = get_settings()
    try:
        conn = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        queue = Queue("locked-in", connection=conn)
        job = queue.enqueue(sync_provider, body.domain)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not enqueue job (is Redis up?): {exc}",
        ) from exc

    return {"job_id": job.id, "domain": body.domain, "status": job.get_status()}


@router.get("/{job_id}")
async def job_status(job_id: str, _: str = Depends(require_api_key)) -> dict:
    settings = get_settings()
    try:
        conn = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        queue = Queue("locked-in", connection=conn)
        job = queue.fetch_job(job_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "status": job.get_status(),
        "result": job.result,
        "exc_info": job.exc_info,
    }
