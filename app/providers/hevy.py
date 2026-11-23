from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.cache import cache_get, cache_set
from app.config import get_settings
from app.providers.base import Provider, ProviderResult

HEVY_BASE = "https://api.hevyapp.com"


# Hevy's public API is Pro-only. Keep the client below for later; do not call it.
HEVY_ON_HOLD = True
HEVY_HOLD_REASON = (
    "Hevy API requires a Pro subscription — gym provider on hold until access is available"
)


class HevyProvider(Provider):
    domain = "gym"

    async def fetch(self) -> ProviderResult:
        if HEVY_ON_HOLD:
            return ProviderResult(
                domain=self.domain,
                available=False,
                error=HEVY_HOLD_REASON,
            )

        settings = get_settings()
        if not settings.hevy_api_key:
            return ProviderResult(
                domain=self.domain,
                available=False,
                error="HEVY_API_KEY not configured",
            )

        cached = cache_get("hevy:summary")
        if cached is not None:
            return ProviderResult(domain=self.domain, available=True, data=cached)

        try:
            workouts = await self._fetch_workouts(settings.hevy_api_key)
            data = self._normalize(workouts)
            cache_set("hevy:summary", data)
            return ProviderResult(domain=self.domain, available=True, data=data)
        except Exception as exc:  # noqa: BLE001 — surface as provider slice error
            return ProviderResult(domain=self.domain, available=False, error=str(exc))

    async def _fetch_workouts(self, api_key: str) -> list[dict[str, Any]]:
        headers = {"api-key": api_key, "Accept": "application/json"}
        workouts: list[dict[str, Any]] = []
        page = 1
        async with httpx.AsyncClient(timeout=30.0) as client:
            while page <= 5:
                response = await client.get(
                    f"{HEVY_BASE}/v1/workouts",
                    headers=headers,
                    params={"page": page, "pageSize": 10},
                )
                if response.status_code == 401:
                    raise RuntimeError("Hevy API rejected the API key")
                response.raise_for_status()
                payload = response.json()
                batch = payload.get("workouts") or payload.get("workout_histories") or []
                if not batch:
                    break
                workouts.extend(batch)
                page += 1
        return workouts

    def _normalize(self, workouts: list[dict[str, Any]]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        dates: list[datetime] = []
        weekly_sets = 0

        for workout in workouts:
            raw = (
                workout.get("start_time")
                or workout.get("created_at")
                or workout.get("date")
            )
            if not raw:
                continue
            try:
                when = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            dates.append(when)
            if when >= week_ago:
                exercises = workout.get("exercises") or []
                for exercise in exercises:
                    sets = exercise.get("sets") or []
                    weekly_sets += len(sets)

        dates.sort(reverse=True)
        streak = self._streak_days(dates, now)
        last = dates[0] if dates else None

        return {
            "workouts_tracked": len(dates),
            "streak_days": streak,
            "weekly_sets": weekly_sets,
            "last_session_at": last.isoformat() if last else None,
            "source": "hevy",
        }

    def _streak_days(self, dates: list[datetime], now: datetime) -> int:
        if not dates:
            return 0
        days = sorted({d.astimezone(timezone.utc).date() for d in dates}, reverse=True)
        streak = 0
        cursor = now.astimezone(timezone.utc).date()
        if days[0] < cursor - timedelta(days=1):
            return 0
        expected = days[0]
        for day in days:
            if day == expected:
                streak += 1
                expected = expected - timedelta(days=1)
            elif day < expected:
                break
        return streak
