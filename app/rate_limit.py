"""Redis sliding-window rate limiter middleware."""

from __future__ import annotations

import time
import uuid
from typing import Callable

import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings


class SlidingWindowRateLimiter:
    def __init__(self, client: redis.Redis, limit: int, window_seconds: int) -> None:
        self.client = client
        self.limit = limit
        self.window_seconds = window_seconds

    def allow(self, key: str) -> tuple[bool, int, int]:
        """Return (allowed, remaining, retry_after_seconds)."""
        now = time.time()
        window_start = now - self.window_seconds
        redis_key = f"rl:{key}"
        member = f"{now}:{uuid.uuid4().hex}"
        pipe = self.client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {member: now})
        pipe.expire(redis_key, self.window_seconds + 1)
        _, count, _, _ = pipe.execute()
        # count is before this request was added
        if count >= self.limit:
            # remove the speculative add
            self.client.zrem(redis_key, member)
            oldest = self.client.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                retry_after = max(1, int(self.window_seconds - (now - oldest[0][1])) + 1)
            else:
                retry_after = self.window_seconds
            return False, 0, retry_after
        remaining = max(0, self.limit - (count + 1))
        return True, remaining, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: redis.Redis | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self.settings = settings
        self._client = redis_client
        self._limiter: SlidingWindowRateLimiter | None = None

    def _get_limiter(self) -> SlidingWindowRateLimiter | None:
        if self._limiter is not None:
            return self._limiter
        try:
            client = self._client or redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
            client.ping()
            self._limiter = SlidingWindowRateLimiter(
                client,
                self.settings.rate_limit_requests,
                self.settings.rate_limit_window_seconds,
            )
            return self._limiter
        except (redis.RedisError, OSError, TimeoutError):
            return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in {
            "/",
            "/dashboard",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }:
            return await call_next(request)

        limiter = self._get_limiter()
        if limiter is None:
            # Fail open if Redis is down so local docs still work; mark degraded via header.
            response = await call_next(request)
            response.headers["X-RateLimit-Degraded"] = "1"
            return response

        client_id = request.headers.get("x-api-key") or (
            request.client.host if request.client else "anonymous"
        )
        allowed, remaining, retry_after = limiter.allow(client_id)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "retry_after": retry_after},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
