from pydantic import BaseModel
from typing import Optional

class GenerationRequest(BaseModel):
    objective: str
    security_level: Optional[str] = "low"
    max_iterations: Optional[int] = 1

class GenerationResponse(BaseModel):
    task_id: str
    status: str
    message: str
