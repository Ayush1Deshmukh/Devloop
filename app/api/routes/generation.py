import logging
import uuid

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.core.agents.builder import agent_app
from app.models.schemas import GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=GenerationResponse)
async def generate_code(request: GenerationRequest):
    init_state = {
        "objective": request.objective,
        "code_content": request.initial_code or "",
        "test_output": "",
        "security_report": "",
        "status": "started",
        "iterations": 0,
        "max_iterations": request.max_iterations,
        "logs": [],
    }

    # agent_app.invoke() is synchronous and can take many seconds. Running it
    # directly in this coroutine would block the event loop for every other
    # request, so hand it to the threadpool.
    try:
        res = await run_in_threadpool(agent_app.invoke, init_state)
    except Exception as e:  # noqa: BLE001 - surface agent failures as a clean 502
        logger.exception("Agent execution failed")
        raise HTTPException(status_code=502, detail=f"Agent execution failed: {e}") from e

    # The agent may short-circuit and omit keys, so read defensively.
    status = res.get("status", "unknown")
    security_report = res.get("security_report") or "Not scanned"

    msg = "Success" if status == "completed" else "Failed after retries"
    if security_report != "Clear":
        msg += f" | Warning: {security_report}"

    return GenerationResponse(
        task_id=str(uuid.uuid4()),
        status=status,
        message=msg,
        code=res.get("code_content") or None,
        iterations=res.get("iterations", 0),
        security_report=security_report,
        logs=res.get("logs", []),
    )
