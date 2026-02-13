from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- REQUEST MODEL ---
# This is what the user MUST send us
class GenerationRequest(BaseModel):
    objective: str = Field(..., min_length=10, description="The coding task to perform")
    initial_code: Optional[str] = Field(None, description="Optional existing code to refactor")
    security_level: str = Field("high", pattern="^(low|medium|high)$")
    max_iterations: int = Field(5, ge=1, le=10)

# --- RESPONSE MODEL ---
# This is what we send back
class GenerationResponse(BaseModel):
    task_id: str
    status: str
    message: str