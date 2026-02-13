from fastapi import APIRouter
from app.models.generation import GenerationRequest, GenerationResponse
from app.core.agents.builder import agent_app
import uuid

router = APIRouter()

@router.post("/generate", response_model=GenerationResponse)
async def generate_code(request: GenerationRequest):
    init_state = {
        "objective": request.objective,
        "code_content": "",
        "test_output": "",
        "security_report": "",
        "status": "started",
        "iterations": 0,
        "logs": []
    }
    
    res = agent_app.invoke(init_state)
    
    msg = "Success" if res["status"] == "completed" else "Failed after retries"
    if res["security_report"] != "Clear":
        msg += f" | Warning: {res['security_report']}"

    return GenerationResponse(
        task_id=str(uuid.uuid4()),
        status=res["status"],
        message=msg
    )