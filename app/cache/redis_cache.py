import hashlib
import json
import logging
from typing import Any, Dict, Optional

import redis

from app.core.config import settings
from app.observability.metrics import CACHE_OPERATIONS

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        # The client is created lazily so importing this module never touches the
        # network — otherwise the whole app fails to import when Redis is down.
        self._redis = None
        self.ttl = 3600  # Cache lives for 1 hour

    @property
    def redis(self):
        if self._redis is None:
            # decode_responses=True ensures we get str back, not bytes.
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def _generate_key(self, prompt: str, security_level: str) -> str:
        """Creates a unique fingerprint for a request."""
        # Normalize input (lowercase) so "Write Code" and "write code" both hit.
        raw_string = f"{prompt.lower().strip()}|{security_level}"
        return f"devloop:cache:{hashlib.sha256(raw_string.encode()).hexdigest()}"

    def get_cached_response(self, prompt: str, security_level: str) -> Optional[Dict[str, Any]]:
        """Checks if we have seen this request before."""
        try:
            key = self._generate_key(prompt, security_level)
            data = self.redis.get(key)

            if data:
                self.redis.incr("devloop:metrics:cache_hits")
                CACHE_OPERATIONS.labels(status="hit").inc()
                return json.loads(data)

            self.redis.incr("devloop:metrics:cache_misses")
            CACHE_OPERATIONS.labels(status="miss").inc()
            return None
        except (redis.RedisError, OSError, json.JSONDecodeError) as e:
            logger.warning("Cache read failed: %s", e)
            return None

    def save_response(self, prompt: str, security_level: str, response_data: Dict[str, Any]):
        """Saves the AI's answer for next time."""
        try:
            key = self._generate_key(prompt, security_level)
            self.redis.setex(key, self.ttl, json.dumps(response_data))
        except (redis.RedisError, OSError, TypeError) as e:
            logger.warning("Cache write failed: %s", e)

    def get_stats(self):
        """Returns the hit/miss ratio."""
        try:
            hits = int(self.redis.get("devloop:metrics:cache_hits") or 0)
            misses = int(self.redis.get("devloop:metrics:cache_misses") or 0)
            total = hits + misses
            return {
                "hits": hits,
                "misses": misses,
                "hit_ratio": f"{(hits / total * 100):.1f}%" if total > 0 else "0%",
            }
        except (redis.RedisError, OSError, ValueError) as e:
            logger.warning("Cache stats unavailable: %s", e)
            return {"status": "Redis unavailable"}


# Export a single instance to be used by the API
cache = CacheService()
