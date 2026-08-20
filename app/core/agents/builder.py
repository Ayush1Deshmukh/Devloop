# A state-machine based agent built with LangGraph. If the generated code fails a
# compilation check or contains unsafe functions like eval(), a conditional edge
# routes the state back to the LLM for a corrected iteration — a self-healing loop
# that runs until the code is both functional and secure, or the budget runs out.
import json
import logging
import re
import urllib.error
import urllib.request
from typing import List, TypedDict

from langgraph.graph import END, StateGraph

from app.core.config import settings

logger = logging.getLogger(__name__)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
REQUEST_TIMEOUT = 60  # seconds — without this urlopen can hang forever
DEFAULT_MAX_ITERATIONS = 5

UNSAFE_PATTERNS = ["os.system", "eval(", "exec(", "subprocess.call", "shutil."]


class DevState(TypedDict, total=False):
    objective: str
    code_content: str
    test_output: str
    security_report: str
    status: str
    iterations: int
    max_iterations: int
    logs: List[str]


class AIError(RuntimeError):
    """Raised when the model cannot be reached or returns nothing usable."""


# Google echoes the offending API key back in some 4xx bodies (e.g. suspended
# key errors). Those bodies reach API responses and logs, so scrub them.
_API_KEY_RE = re.compile(r"AIza[0-9A-Za-z_\-]{10,}")


def _redact(text: str) -> str:
    return _API_KEY_RE.sub("AIza***REDACTED***", text)


def ask_ai(prompt: str) -> str:
    """Calls Gemini and returns raw generated text.

    Raises AIError instead of returning the error message as if it were code —
    otherwise the failure text gets written out as the "solution" and the agent
    burns its whole retry budget trying to fix an error string.
    """
    # Read the key at call time, not import time: settings loads .env, and an
    # import-time os.getenv() would capture None before the env was populated.
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise AIError("GOOGLE_API_KEY is not configured.")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "SYSTEM: You are an expert Python coder. Return ONLY raw code "
                            f"without markdown blocks or explanations.\nUSER: {prompt}"
                        )
                    }
                ]
            }
        ]
    }

    req = urllib.request.Request(
        API_URL.format(model=settings.LLM_MODEL),
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            # Sent as a header rather than a query string so the key does not
            # end up in proxy logs or error messages.
            "x-goog-api-key": api_key,
        },
    )

    try:
        # URL is the hardcoded https Gemini endpoint; only the model name (a path
        # segment from our own settings) is interpolated, so no scheme injection.
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:  # nosec B310
            res = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = _redact(e.read().decode(errors="replace"))[:500]
        raise AIError(f"Gemini returned HTTP {e.code}: {detail}") from e
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise AIError(f"Could not reach Gemini: {_redact(str(e))}") from e

    try:
        return res["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as e:
        # Happens when a response is blocked by safety filters or truncated.
        raise AIError(f"Unexpected Gemini response shape: {_redact(json.dumps(res))[:500]}") from e


def _strip_markdown(text: str) -> str:
    return text.replace("```python", "").replace("```", "").strip()


def developer_node(state: DevState):
    iters = state.get("iterations", 0)
    logs = list(state.get("logs", []))

    if state.get("test_output"):
        prompt = (
            "The previous code failed. Fix it.\n"
            f"CODE:\n{state.get('code_content', '')}\n"
            f"ERROR:\n{state['test_output']}"
        )
    else:
        prompt = f"Write a robust Python solution for: {state['objective']}"

    try:
        code = _strip_markdown(ask_ai(prompt))
    except AIError as e:
        logger.error("AI call failed on iteration %s: %s", iters + 1, e)
        return {
            "iterations": iters + 1,
            "status": "error",
            "test_output": str(e),
            "logs": logs + [f"❌ AI call failed: {e}"],
        }

    return {
        "code_content": code,
        "iterations": iters + 1,
        "logs": logs + [f"Iteration {iters + 1}"],
    }


def security_node(state: DevState):
    # An upstream AI failure means there is nothing to scan; don't overwrite the
    # error status with a bogus "Clear".
    if state.get("status") == "error":
        return {"security_report": "Not scanned"}

    code = state.get("code_content", "")
    for pattern in UNSAFE_PATTERNS:
        if pattern in code:
            return {"security_report": f"Unsafe function detected: {pattern}"}
    return {"security_report": "Clear"}


def tester_node(state: DevState):
    if state.get("status") == "error":
        return {}  # Terminal: the router will stop the graph.

    iterations = state.get("iterations", 0)
    budget = state.get("max_iterations") or DEFAULT_MAX_ITERATIONS
    has_budget = iterations < budget

    report = state.get("security_report", "Clear")
    if report != "Clear":
        # Previously this retried unconditionally, so a persistent security
        # finding looped until LangGraph's recursion limit blew up.
        return {
            "status": "retry" if has_budget else "failed",
            "test_output": f"Security Violation: {report}",
        }

    try:
        compile(state.get("code_content", ""), "solution.py", "exec")
    except SyntaxError as e:
        return {"status": "retry" if has_budget else "failed", "test_output": str(e)}

    return {"status": "completed", "test_output": "Passed"}


def router(state: DevState):
    return "developer" if state.get("status") == "retry" else END


# Define Workflow
workflow = StateGraph(DevState)
workflow.add_node("developer", developer_node)
workflow.add_node("security", security_node)
workflow.add_node("tester", tester_node)

workflow.set_entry_point("developer")
workflow.add_edge("developer", "security")
workflow.add_edge("security", "tester")
workflow.add_conditional_edges("tester", router, {"developer": "developer", END: END})

agent_app = workflow.compile()
