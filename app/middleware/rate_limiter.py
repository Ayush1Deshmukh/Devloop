# personal project and you want to keep it free, Rate Limiting is actually your best friend. It prevents accidental bugs (like an infinite loop) from draining your free Google Gemini API quota or crashing your computer.
import time
import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE  # e.g., 60 req/min
        self.window = 60  # 60 seconds
        
        # Try connecting to Redis
        try:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis.ping()
            self.use_redis = True
            print("✅ Rate Limiter: Connected to Redis")
        except:
            self.use_redis = False
            self.memory_store = {}  # Fallback for free local usage
            print("⚠️ Rate Limiter: Redis unavailable. Using In-Memory Fallback.")

    async def dispatch(self, request: Request, call_next):
        # 1. Identify the user (by IP address)
        client_ip = request.client.host
        
        # 2. Check if this path should be limited
        if request.url.path == "/health" or request.url.path.startswith("/docs"):
            return await call_next(request)

        # 3. Check Limits
        if self.use_redis:
            allowed, remaining = self._check_redis(client_ip)
        else:
            allowed, remaining = self._check_memory(client_ip)

        # 4. Block if limit exceeded
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"error": "Too Many Requests", "detail": "Slow down! You hit the free tier limit."}
            )

        # 5. Process request and add headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _check_redis(self, ip: str):
        key = f"rate_limit:{ip}"
        current = self.redis.incr(key)
        if current == 1:
            self.redis.expire(key, self.window)
        
        remaining = max(0, self.rate_limit - current)
        return current <= self.rate_limit, remaining

    def _check_memory(self, ip: str):
        current_time = time.time()
        # Clean old records
        if ip not in self.memory_store:
            self.memory_store[ip] = []
        
        # Keep only timestamps within the last 60 seconds
        self.memory_store[ip] = [t for t in self.memory_store[ip] if t > current_time - self.window]
        
        # Check count
        count = len(self.memory_store[ip])
        if count >= self.rate_limit:
            return False, 0
        
        # Add new request
        self.memory_store[ip].append(current_time)
        return True, self.rate_limit - (count + 1)