from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.providers.hevy import HevyProvider
from app.providers.leetcode import LeetCodeProvider

router = APIRouter(prefix="/v1", tags=["me"])


@router.get("/me/summary")
async def me_summary(_: str = Depends(require_api_key)) -> dict:
    gym = await HevyProvider().fetch()
    leetcode = await LeetCodeProvider().fetch()

    locked_in = {
        "gym_streak_days": gym.data.get("streak_days") if gym.available else None,
        "leetcode_total_solved": leetcode.data.get("total_solved") if leetcode.available else None,
        "domains_online": [p.domain for p in (gym, leetcode) if p.available],
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "locked_in": locked_in,
        "gym": gym.model_dump(),
        "leetcode": leetcode.model_dump(),
    }
