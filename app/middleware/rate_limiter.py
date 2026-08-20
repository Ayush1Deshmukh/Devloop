# Rate limiting keeps a personal project free: it stops accidental bugs (like an
# infinite loop) from draining the free Google Gemini quota or pinning the host.
import logging
import time

import redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

# Operational endpoints must stay reachable even when a client is being throttled.
EXEMPT_PATHS = ("/health", "/metrics", "/docs", "/redoc", "/openapi.json")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # seconds
        self.memory_store = {}  # always available, used as the fallback

        try:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis.ping()
            self.use_redis = True
            logger.info("Rate Limiter: connected to Redis")
        except (redis.RedisError, OSError, ValueError) as e:
            self.redis = None
            self.use_redis = False
            logger.warning("Rate Limiter: Redis unavailable (%s). Using in-memory fallback.", e)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in EXEMPT_PATHS or path.startswith("/docs"):
            return await call_next(request)

        # request.client is None for ASGI transports that don't report a peer
        # (some test clients, certain proxies) — guard rather than crash.
        client_ip = request.client.host if request.client else "unknown"

        allowed, remaining = self._check(client_ip)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": "Slow down! You hit the free tier limit.",
                },
                headers={
                    "X-RateLimit-Limit": str(self.rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(self.window),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _check(self, ip: str):
        if self.use_redis:
            try:
                return self._check_redis(ip)
            except redis.RedisError as e:
                # Redis was reachable at startup but died since. Degrade to the
                # in-memory counter instead of 500-ing every request.
                logger.warning("Rate Limiter: Redis failed mid-flight (%s). Falling back.", e)
                self.use_redis = False
        return self._check_memory(ip)

    def _check_redis(self, ip: str):
        key = f"rate_limit:{ip}"
        # Pipeline so the counter and its TTL are set atomically; without the
        # expire, a key set during a failed request would never reset.
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window, nx=True)
        current = pipe.execute()[0]

        remaining = max(0, self.rate_limit - current)
        return current <= self.rate_limit, remaining

    def _check_memory(self, ip: str):
        current_time = time.time()
        window_start = current_time - self.window

        timestamps = [t for t in self.memory_store.get(ip, []) if t > window_start]
        self.memory_store[ip] = timestamps

        if len(timestamps) >= self.rate_limit:
            return False, 0

        timestamps.append(current_time)
        return True, self.rate_limit - len(timestamps)
