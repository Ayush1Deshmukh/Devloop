from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "DevLoop API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Updated to allow both local dev and Docker networking
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    # --- SECURITY FIX: No hardcoded secrets ---
    # We set these to None so Pydantic is forced to look at the .env file or environment
    GOOGLE_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"

    # Default to the service name used in docker-compose
    REDIS_URL: str = "redis://devloop-redis:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 20
    SANDBOX_CONTAINER_NAME: str = "devloop-sandbox"

    # This tells Pydantic to read the .env file automatically
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True, 
        extra="ignore"
    )

settings = Settings()