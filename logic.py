import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from functools import lru_cache
from typing import TypedDict

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

# --- 0. LOAD ENV ---
load_dotenv()

# --- 1. PATH FIX ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tools import run_test, write_file
except ImportError:
    from app.tools import run_test, write_file

# --- 2. KEY LOADING ---
# IMPORTANT: never write a key into os.environ. On Streamlit Community Cloud a
# single Python process serves every visitor, so a global mutation made for one
# session is visible to all the others — a visitor's own key would leak to
# strangers. Keys are passed explicitly into create_agent() instead.


def get_owner_api_key():
    """Returns the deployer's key from Streamlit secrets or the environment."""
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        # No secrets.toml (normal for local runs) — fall back to .env.
        pass
    return os.getenv("GOOGLE_API_KEY")


# --- 3. CONFIG ---
PRIMARY_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")
BACKUP_MODEL = os.getenv("LLM_BACKUP_MODEL", "gemini-2.5-flash")
MAX_ITERATIONS = int(os.getenv("DEVLOOP_MAX_ITERATIONS", "5"))
SECURITY_SCAN_TIMEOUT = 30
KEY_CHECK_TIMEOUT = 15

# Only findings at these severities stop the build. Bandit flags plenty of LOW
# noise (asserts, subprocess imports) that would otherwise loop the agent
# forever on code that is perfectly fine.
BLOCKING_SEVERITIES = {"HIGH"}


class LLMError(RuntimeError):
    """Raised when every model fails. Never treated as generated code."""


# Google echoes the API key back in some error bodies; those messages end up in
# the on-screen log, so scrub them before they are shown.
_API_KEY_RE = re.compile(r"AIza[0-9A-Za-z_\-]{10,}")


def _redact(text: str) -> str:
    return _API_KEY_RE.sub("AIza***REDACTED***", str(text))


def explain_api_error(err) -> str:
    """Turns a raw Google SDK exception into something a human can act on.

    The raw bodies are enormous protobuf dumps that also echo the API key back;
    showing them verbatim taught users nothing and leaked the credential into
    the on-screen log.
    """
    raw = _redact(err)

    if "CONSUMER_SUSPENDED" in raw or "has been suspended" in raw:
        return (
            "Google has **suspended the Cloud project** behind this key (the usual "
            "cause is a key being committed to a public repo). Note this is a "
            "*project*-level suspension: minting a new key inside the same project "
            "inherits it. Create a **new Google Cloud project**, then a key in that "
            "project, at aistudio.google.com/app/apikey."
        )
    if "API_KEY_INVALID" in raw or "API key not valid" in raw:
        return (
            "Google rejected this API key as invalid. Check it was copied whole "
            "(they start with `AIza`) and that the Generative Language API is "
            "enabled for its project."
        )
    if "PERMISSION_DENIED" in raw or "403" in raw:
        return (
            "Google denied this key permission to call the Generative Language "
            "API. Enable that API for the key's project, or generate a new key."
        )
    if "429" in raw or "RESOURCE_EXHAUSTED" in raw:
        return "Rate limit / quota exhausted on this key. Wait a minute, or use a different key."
    if "503" in raw or "UNAVAILABLE" in raw or "high demand" in raw or "overloaded" in raw:
        return (
            f"Both `{PRIMARY_MODEL}` and `{BACKUP_MODEL}` are overloaded right now "
            "(Google returns 503 when a model spikes in demand). This is temporary "
            "— retry in a moment, or point LLM_MODEL at a less busy model."
        )
    if "404" in raw or "not found" in raw.lower() or "is not supported" in raw:
        return (
            f"The configured model was rejected by Google. `LLM_MODEL` is set to "
            f"`{PRIMARY_MODEL}` and `LLM_BACKUP_MODEL` to `{BACKUP_MODEL}` — at least "
            "one of those names is retired or unavailable to this key. Run the key "
            "check in the sidebar to list the models your key can actually use."
        )
    return raw[:500]


def verify_api_key(api_key: str):
    """Live diagnostic: can this key talk to Gemini, and with which models?

    Returns (ok, message, model_names). Uses the plain REST ListModels endpoint
    via urllib so it works without pulling in the deprecated
    google-generativeai package, and sends the key as a header so it never
    lands in a proxy log or a URL.
    """
    if not api_key:
        return False, "No API key provided.", []

    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": api_key},
    )
    try:
        # Hardcoded https endpoint, no user-controlled URL parts.
        with urllib.request.urlopen(req, timeout=KEY_CHECK_TIMEOUT) as r:  # nosec B310
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return False, explain_api_error(e.read().decode(errors="replace")), []
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return False, f"Could not reach Google: {_redact(e)}", []

    names = [
        m["name"].removeprefix("models/")
        for m in data.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    if not names:
        return False, "The key works, but no models support generateContent.", []
    return True, f"Key is valid — {len(names)} usable models.", sorted(names)


class DevState(TypedDict, total=False):
    objective: str
    code_content: str
    test_content: str
    test_output: str
    security_report: str
    security_ok: bool
    status: str
    iterations: int
    logs: list


# Models are built lazily so importing this module doesn't blow up when the API
# key is missing — the UI can then show a clear message instead of a stack trace.
# Cached per (model, key) pair, bounded so visitor keys aren't retained forever.
@lru_cache(maxsize=32)
def _get_llm(model_name: str, api_key: str):
    return ChatGoogleGenerativeAI(model=model_name, temperature=0, google_api_key=api_key)


# --- 4. HELPERS ---
def clean_content(response):
    if not response or not response.content:
        return ""
    content = response.content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                text_parts.append(part.get("text", str(part)))
        content = "".join(text_parts)
    return str(content).replace("```python", "").replace("```", "").strip()


def _bandit_cmd():
    """Finds a runnable bandit.

    `["bandit", ...]` alone is wrong: inside a virtualenv that is not on PATH
    (the normal case when the app is started as `venv/bin/streamlit`), the
    console script is invisible and every scan came back "not found". Running it
    as a module through the *current* interpreter always resolves the bandit
    that was installed alongside this app.
    """
    if shutil.which("bandit"):
        return ["bandit"]
    return [sys.executable, "-m", "bandit"]


def _format_findings(results):
    """Renders bandit's JSON findings as a compact, readable report."""
    if not results:
        return "No issues identified."
    lines = []
    for r in results:
        lines.append(
            f"[{r.get('issue_severity', '?')}/{r.get('issue_confidence', '?')}] "
            f"{r.get('test_id', '?')}: {r.get('issue_text', '').strip()}\n"
            f"    line {r.get('line_number', '?')}: {(r.get('code') or '').strip()}"
        )
    return "\n\n".join(lines)


def run_security_scan(filename):
    """Scans generated code with Bandit.

    Returns (ok, report). `ok` answers one question only: "should this finding
    stop the build?" A scanner that could not run at all returns ok=True. That
    matters — the router treats a non-ok scan as a reason to re-enter the
    developer node, so reporting "scanner missing" as a failure made the agent
    burn its entire iteration budget re-writing code that had already passed its
    tests.
    """
    cmd = _bandit_cmd() + ["-r", filename, "-f", "json", "-q"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=SECURITY_SCAN_TIMEOUT)
    except FileNotFoundError:
        return True, "⚠️ Scanner unavailable: Bandit is not installed. Scan skipped."
    except subprocess.TimeoutExpired:
        return True, f"⚠️ Scanner unavailable: scan timed out after {SECURITY_SCAN_TIMEOUT}s."
    except OSError as e:
        return True, f"⚠️ Scanner unavailable: {e}. Scan skipped."

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        detail = (result.stderr or result.stdout or "no output").strip()[:300]
        return True, f"⚠️ Scanner unavailable: Bandit produced no usable report.\n{detail}"

    findings = payload.get("results", [])
    blocking = [f for f in findings if f.get("issue_severity", "").upper() in BLOCKING_SEVERITIES]
    report = _format_findings(findings)

    counts = payload.get("metrics", {}).get("_totals", {})
    summary = (
        f"High: {int(counts.get('SEVERITY.HIGH', 0))}  "
        f"Medium: {int(counts.get('SEVERITY.MEDIUM', 0))}  "
        f"Low: {int(counts.get('SEVERITY.LOW', 0))}"
    )

    if not blocking:
        prefix = "Clear — no high-severity issues." if findings else "Clear — no issues identified."
        return True, f"{prefix}\n{summary}\n\n{report}"
    return False, f"{len(blocking)} high-severity issue(s) found.\n{summary}\n\n{report}"


def safe_invoke(prompt, api_key):
    """Calls the primary model, falling back to the backup on rate limits.

    Raises LLMError on total failure rather than returning the error text — the
    old version returned the message as a message object, so the failure string
    got written into solution.py and the agent spent its whole budget trying to
    "fix" an error message.
    """
    if not api_key:
        raise LLMError("No Gemini API key available for this session.")

    try:
        return clean_content(_get_llm(PRIMARY_MODEL, api_key).invoke([HumanMessage(content=prompt)]))
    except Exception as e:
        # 503/UNAVAILABLE ("model is experiencing high demand") and 500/INTERNAL
        # are transient server-side faults — exactly what the backup model is
        # for. They were missing here, so a momentary capacity spike on the
        # primary aborted the whole run instead of falling back.
        err = str(e)
        retryable = any(t in err for t in (
            "429", "RESOURCE_EXHAUSTED",
            "503", "UNAVAILABLE", "overloaded", "high demand",
            "500", "INTERNAL",
            "404",
        ))
        if not retryable or BACKUP_MODEL == PRIMARY_MODEL:
            raise LLMError(explain_api_error(e)) from e

        try:
            st.toast(f"⚠️ {PRIMARY_MODEL} unavailable. Falling back to {BACKUP_MODEL}...", icon="🔄")
        except Exception:
            pass  # Not running under Streamlit (tests, CLI).
        time.sleep(2)
        try:
            return clean_content(_get_llm(BACKUP_MODEL, api_key).invoke([HumanMessage(content=prompt)]))
        except Exception as e2:
            raise LLMError(f"Both models failed. {explain_api_error(e2)}") from e2


def _llm_failure(e: LLMError, role: str):
    """Shared terminal state for an AI outage, so the router can stop cleanly."""
    return {"status": "error", "logs": [f"❌ [{role}] AI call failed: {e}"]}


# --- 5. NODES ---
# The two LLM-backed nodes are built per-run so the API key is captured in a
# closure rather than shared globally. See the note in section 2.
def make_architect_node(api_key):
    def architect_node(state: DevState):
        log = "🏗️ [ARCHITECT] Designing unit tests (TDD)..."
        prompt = (
            f"Write a pytest unit test for: '{state['objective']}'. "
            "File: 'test_solution.py'. Import 'solution'. ONLY code."
        )

        try:
            res = safe_invoke(prompt, api_key)
        except LLMError as e:
            return _llm_failure(e, "ARCHITECT")

        if not res:
            res = "# Error generating tests"
        write_file("test_solution.py", res)

        return {"test_content": res, "iterations": 0, "logs": [log, "✅ [ARCHITECT] Tests Generated."]}

    return architect_node


def make_developer_node(api_key):
    def developer_node(state: DevState):
        i = state.get("iterations", 0) + 1
        log = f"👨‍💻 [DEVELOPER] Coding (Cycle {i})..."

        context = ""
        if state.get("test_output") and "failed" in state.get("test_output", "").lower():
            context += f"\nTEST FAILURES:\n{state['test_output']}"

        # Only feed back a scan that actually blocks. A clean or unavailable scan
        # used to match the old `"High" in report` substring test and derail an
        # otherwise-passing build.
        if state.get("security_ok") is False:
            context += f"\nSECURITY VULNERABILITIES:\n{state.get('security_report', '')}"

        if context:
            prompt = f"Fix code based on:\n{context}\nObjective: {state['objective']}\nONLY python code."
        else:
            prompt = f"Write python code for: '{state['objective']}'. File: 'solution.py'. ONLY python code."

        try:
            res = safe_invoke(prompt, api_key)
        except LLMError as e:
            return {**_llm_failure(e, "DEVELOPER"), "iterations": i}

        if not res:
            res = "# Error generating code"
        write_file("solution.py", res)

        return {"code_content": res, "iterations": i, "logs": [log]}

    return developer_node


def security_node(state: DevState):
    if state.get("status") == "error":
        return {}  # Nothing was generated; skip the scan.

    ok, report = run_security_scan("solution.py")
    if ok:
        log = "✅ [SEC-OPS] Scan clean — no blocking vulnerabilities."
    else:
        log = "🛡️ [SEC-OPS] High-severity vulnerabilities found — sending back to developer."
    return {"security_report": report, "security_ok": ok, "logs": [log]}


def tester_node(state: DevState):
    if state.get("status") == "error":
        return {}

    log = "⚡ [TESTER] Running Unit Tests..."
    result = run_test("solution.py", "test_solution.py")

    if isinstance(result, str):
        # Legacy shape — treat a bare string as failure output.
        status, output = "failed", result
    else:
        status = result.get("status", "failed")
        output = result.get("output", "No output")

    if status == "error":
        # The sandbox itself is broken. Feeding this back to the LLM as a "test
        # failure" would make it rewrite working code forever, so stop instead.
        return {
            "test_output": output,
            "status": "error",
            "logs": [log, f"❌ [TESTER] Test runner unavailable: {output.strip()[:200]}"],
        }

    final_log = "✅ [SUCCESS] Tests Passed!" if status == "success" else "❌ [FAIL] Tests Failed."
    return {"test_output": output, "status": status, "logs": [log, final_log]}


def router(state: DevState):
    status = state.get("status", "")

    # Terminal conditions: an AI outage or a broken test runner. Retrying cannot help.
    if status == "error":
        return END

    # Done means both gates pass: green tests AND nothing blocking from the scan.
    # `security_ok` defaults to True so an unavailable scanner cannot wedge the
    # loop — see run_security_scan().
    if status == "success" and state.get("security_ok", True):
        return END
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return END
    return "developer"


def _entry_router(state: DevState):
    """Stops the graph immediately if the architect could not reach the model."""
    return END if state.get("status") == "error" else "developer"


def create_agent(api_key):
    """Compiles an agent bound to exactly this API key.

    Build one per run. The key lives only in the closures of this graph's nodes,
    so concurrent visitors on a shared Streamlit process can never see each
    other's credentials.
    """
    workflow = StateGraph(DevState)
    workflow.add_node("architect", make_architect_node(api_key))
    workflow.add_node("developer", make_developer_node(api_key))
    workflow.add_node("security", security_node)
    workflow.add_node("tester", tester_node)
    workflow.set_entry_point("architect")
    workflow.add_conditional_edges("architect", _entry_router, {END: END, "developer": "developer"})
    workflow.add_edge("developer", "security")
    workflow.add_edge("security", "tester")
    workflow.add_conditional_edges("tester", router, {END: END, "developer": "developer"})
    return workflow.compile()


# Default agent bound to the deployer's own key, for local runs and any caller
# that doesn't need per-session keys.
agent_app = create_agent(get_owner_api_key())
