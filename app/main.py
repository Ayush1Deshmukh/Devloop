from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import generation
from app.observability.metrics import PrometheusMiddleware, metrics_endpoint
from app.middleware.rate_limiter import RateLimitMiddleware

# 1. Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 2. Setup Middleware (Order Matters!)
# In FastAPI, the middleware added LAST runs FIRST.

# C. Metrics (Added LAST -> Runs FIRST)
# We want this on the outside so it captures EVERYTHING, including Rate Limit blocks.
app.add_middleware(PrometheusMiddleware)

# B. Rate Limiter (Added Middle -> Runs Second)
# This sits inside the metrics, but outside the app.
app.add_middleware(RateLimitMiddleware)

# A. CORS (Added First -> Runs Last)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 3. Register Routes
app.include_router(generation.router, prefix=settings.API_V1_STR, tags=["Generation"])

# 4. Metrics Endpoint
app.add_route("/metrics", metrics_endpoint)

# 5. Health Check


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "llm_model": settings.LLM_MODEL
    }


@app.get("/")
def root():
    return {"message": "Welcome to DevLoop v2.0 API. Visit /docs for documentation."}
