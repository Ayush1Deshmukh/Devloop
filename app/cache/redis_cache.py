from app.observability.metrics import CACHE_OPERATIONS
import redis
import json
import hashlib
from app.core.config import settings
from typing import Optional, Dict, Any

class CacheService:
    def __init__(self):
        # Connect to the Redis database
        # decode_responses=True ensures we get Strings back, not Bytes
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl = 3600  # Cache lives for 1 hour (3600 seconds)

    def _generate_key(self, prompt: str, security_level: str) -> str:
        """
        Creates a unique fingerprint for a request.
        """
        # Normalize input (lowercase) so "Write Code" and "write code" allow a cache hit
        raw_string = f"{prompt.lower().strip()}|{security_level}"
        # Create a SHA256 hash to keep keys short and consistent
        return f"devloop:cache:{hashlib.sha256(raw_string.encode()).hexdigest()}"

    def get_cached_response(self, prompt: str, security_level: str) -> Optional[Dict[str, Any]]:
        """Checks if we have seen this request before."""
        try:
            key = self._generate_key(prompt, security_level)
            data = self.redis.get(key)
            
            if data:
                # Increment 'hits' counter for metrics
                self.redis.incr("devloop:metrics:cache_hits")

                CACHE_OPERATIONS.labels(status="hit").inc()
                return json.loads(data)
            
            self.redis.incr("devloop:metrics:cache_misses")
            CACHE_OPERATIONS.labels(status="miss").inc()
            
            return None
        except Exception as e:
            print(f"⚠️ Cache Error: {e}")
            return None

    def save_response(self, prompt: str, security_level: str, response_data: Dict[str, Any]):
        """Saves the AI's answer for next time."""
        try:
            key = self._generate_key(prompt, security_level)
            # setex = Set with Expiration (TTL)
            self.redis.setex(key, self.ttl, json.dumps(response_data))
        except Exception as e:
            print(f"⚠️ Cache Save Error: {e}")

    def get_stats(self):
        """Returns the hit/miss ratio to prove it's working."""
        try:
            hits = int(self.redis.get("devloop:metrics:cache_hits") or 0)
            misses = int(self.redis.get("devloop:metrics:cache_misses") or 0)
            total = hits + misses
            return {
                "hits": hits,
                "misses": misses,
                "hit_ratio": f"{(hits / total * 100):.1f}%" if total > 0 else "0%"
            }
        except:
            return {"status": "Redis unavailable"}

# Export a single instance to be used by the API
cache = CacheService()