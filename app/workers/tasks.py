from __future__ import annotations

import asyncio
from typing import Any

from app.cache import cache_set
from app.providers.hevy import HevyProvider
from app.providers.leetcode import LeetCodeProvider


def sync_provider(domain: str) -> dict[str, Any]:
    """RQ job: refresh a provider and warm the cache."""
    return asyncio.run(_sync_async(domain))


async def _sync_async(domain: str) -> dict[str, Any]:
    if domain == "gym":
        result = await HevyProvider().fetch()
    elif domain == "leetcode":
        result = await LeetCodeProvider().fetch()
    else:
        return {"ok": False, "error": f"unknown domain {domain}"}

    if result.available:
        cache_set(f"job:{domain}:last", result.data)
    return result.model_dump()
