from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone

import redis

from app.config import settings

_redis_client = None
_redis_failed_at = 0.0
REDIS_RETRY_SECONDS = 5.0


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_redis():
    global _redis_client, _redis_failed_at
    if _redis_client is not None:
        return _redis_client
    now = time.monotonic()
    if _redis_failed_at and now - _redis_failed_at < REDIS_RETRY_SECONDS:
        return None
    try:
        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1, decode_responses=True)
        client.ping()
        _redis_client = client
        _redis_failed_at = 0.0
    except Exception:
        _redis_client = None
        _redis_failed_at = now
    return _redis_client


def reset_redis_cache() -> None:
    global _redis_client, _redis_failed_at
    _redis_client = None
    _redis_failed_at = 0.0


class MemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window = window_seconds
        self.hits: dict[str, deque] = {}

    def allow(self, key: str, now: float | None = None) -> bool:
        import time

        moment = time.monotonic() if now is None else now
        bucket = self.hits.setdefault(key, deque())
        while bucket and moment - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(moment)
        return True


_memory = MemoryRateLimiter(limit=10_000)


def limit_for(plan: str, kind: str) -> int:
    if settings.app_env == "test":
        return 100_000
    from app.security import PLANS

    plan_limit = PLANS.get(plan, PLANS["free"])["searches_per_minute"]
    if kind == "login":
        return 20
    return plan_limit


def allow(key: str, limit: int) -> bool:
    global _redis_client, _redis_failed_at
    if limit >= 100_000:
        return True
    client = get_redis()
    if client is not None:
        try:
            window = int(datetime.now(timezone.utc).timestamp() // 60)
            redis_key = f"rl:{key}:{window}"
            count = client.incr(redis_key)
            if count == 1:
                client.expire(redis_key, 70)
            return count <= limit
        except Exception:
            _redis_client = None
            _redis_failed_at = time.monotonic()
    return _shared_memory_allow(key, limit)


_shared: dict[str, MemoryRateLimiter] = {}


def _shared_memory_allow(key: str, limit: int) -> bool:
    limiter = _shared.get(limit)
    if limiter is None:
        limiter = MemoryRateLimiter(limit)
        _shared[limit] = limiter
    return limiter.allow(key)
