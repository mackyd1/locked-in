from __future__ import annotations

from typing import Any

import httpx

from app.cache import cache_get, cache_set
from app.config import get_settings
from app.providers.base import Provider, ProviderResult

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

PROFILE_QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      reputation
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
  recentAcSubmissionList(username: $username, limit: 5) {
    title
    titleSlug
    timestamp
  }
}
"""


class LeetCodeProvider(Provider):
    domain = "leetcode"

    async def fetch(self) -> ProviderResult:
        settings = get_settings()
        username = settings.leetcode_username.strip()
        if not username:
            return ProviderResult(
                domain=self.domain,
                available=False,
                error="LEETCODE_USERNAME not configured",
            )

        cache_key = f"leetcode:{username}"
        cached = cache_get(cache_key)
        if cached is not None:
            return ProviderResult(domain=self.domain, available=True, data=cached)

        try:
            raw = await self._fetch_profile(username)
            data = self._normalize(username, raw)
            cache_set(cache_key, data)
            return ProviderResult(domain=self.domain, available=True, data=data)
        except Exception as exc:  # noqa: BLE001
            return ProviderResult(domain=self.domain, available=False, error=str(exc))

    async def _fetch_profile(self, username: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LEETCODE_GRAPHQL,
                json={"query": PROFILE_QUERY, "variables": {"username": username}},
                headers={
                    "Content-Type": "application/json",
                    "Referer": f"https://leetcode.com/u/{username}/",
                    "User-Agent": "locked-in/0.1",
                },
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("errors"):
                raise RuntimeError(str(payload["errors"]))
            return payload.get("data") or {}

    def _normalize(self, username: str, raw: dict[str, Any]) -> dict[str, Any]:
        user = raw.get("matchedUser") or {}
        if not user:
            raise RuntimeError(f"LeetCode user not found: {username}")

        counts = {"All": 0, "Easy": 0, "Medium": 0, "Hard": 0}
        for row in (user.get("submitStatsGlobal") or {}).get("acSubmissionNum") or []:
            difficulty = row.get("difficulty") or "All"
            counts[difficulty] = int(row.get("count") or 0)

        recent = [
            {
                "title": item.get("title"),
                "slug": item.get("titleSlug"),
                "timestamp": item.get("timestamp"),
            }
            for item in (raw.get("recentAcSubmissionList") or [])
        ]

        profile = user.get("profile") or {}
        return {
            "username": user.get("username") or username,
            "ranking": profile.get("ranking"),
            "total_solved": counts.get("All", 0),
            "easy": counts.get("Easy", 0),
            "medium": counts.get("Medium", 0),
            "hard": counts.get("Hard", 0),
            "recent_ac": recent,
            "source": "leetcode",
        }
