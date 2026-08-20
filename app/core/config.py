import json
from typing import Annotated, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DevLoop API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # Allows local dev, Docker networking, and a deployed Streamlit front end.
    # NoDecode stops pydantic-settings from JSON-decoding the env value before
    # our validator sees it — without it, a plain comma-separated value raises
    # SettingsError at import and the whole API fails to start.
    BACKEND_CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:8501",
        "http://localhost:3000",
    ]

    # --- SECURITY FIX: No hardcoded secrets ---
    # None so Pydantic is forced to read .env or the environment.
    GOOGLE_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-2.0-flash"

    # Defaults to the docker-compose service name. On free hosting, point this at
    # a managed instance — Upstash gives a free `rediss://` URL, and redis-py
    # negotiates TLS from that scheme automatically.
    REDIS_URL: str = "redis://devloop-redis:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 20
    SANDBOX_CONTAINER_NAME: str = "devloop-sandbox"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        """Accepts either a JSON array or a plain comma-separated list."""
        if not isinstance(v, str):
            return v
        v = v.strip()
        if v.startswith("["):
            return json.loads(v)
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
