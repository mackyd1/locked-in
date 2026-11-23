from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_api_key
from app.providers.base import Provider
from app.providers.hevy import HevyProvider
from app.providers.leetcode import LeetCodeProvider

router = APIRouter(prefix="/v1/stats", tags=["stats"])

PROVIDERS: dict[str, type[Provider]] = {
    "gym": HevyProvider,
    "leetcode": LeetCodeProvider,
}


@router.get("/{domain}")
async def stats_domain(domain: str, _: str = Depends(require_api_key)) -> dict:
    provider_cls = PROVIDERS.get(domain)
    if not provider_cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown domain '{domain}'. Try: {', '.join(sorted(PROVIDERS))}",
        )
    result = await provider_cls().fetch()
    return result.model_dump()
