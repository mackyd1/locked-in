"""Simple Redis JSON cache for provider payloads."""

from __future__ import annotations

import json
from typing import Any

import redis

from app.config import get_settings


def get_redis() -> redis.Redis:
    return redis.from_url(
        get_settings().redis_url,
        decode_responses=True,
        socket_connect_timeout=0.5,
        socket_timeout=0.5,
    )


def cache_get(key: str) -> Any | None:
    try:
        raw = get_redis().get(f"cache:{key}")
    except redis.RedisError:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    settings = get_settings()
    try:
        get_redis().setex(
            f"cache:{key}",
            ttl or settings.cache_ttl_seconds,
            json.dumps(value),
        )
    except redis.RedisError:
        return
