from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response, Request  # <--- Added Request import
import time

# --- 1. Define the Metrics ---

# Counts every single request (Good for tracking volume)
REQUEST_COUNT = Counter(
    "devloop_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

# Measures how long requests take (Good for performance tracking)
REQUEST_LATENCY = Histogram(
    "devloop_http_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint"]
)

# Counts cache hits/misses (Proves your Redis is working)
CACHE_OPERATIONS = Counter(
    "devloop_cache_ops_total",
    "Cache Hits and Misses",
    ["status"] # hit or miss
)

# --- 2. Create the Middleware ---
# This sits between the user and the API to record data automatically
class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate time taken
        process_time = time.time() - start_time
        
        # Record the data
        endpoint = request.url.path
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            endpoint=endpoint
        ).observe(process_time)
        
        return response

# --- 3. The Endpoint ---
# FIXED: Added 'request: Request' argument below
def metrics_endpoint(request: Request):
    """Exposes the data for Prometheus to scrape."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)