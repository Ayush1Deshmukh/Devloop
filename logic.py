import os
import subprocess
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import streamlit as st

# --- PATH SAFE IMPORTS ---
try:
    from tools import write_file, run_test
except ImportError:
    from app.tools import write_file, run_test

# --- API KEY ---
if "GOOGLE_API_KEY" not in os.environ:
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    except FileNotFoundError: pass

# --- CONFIG (AUTO-FALLBACK STRATEGY) ---
def get_working_llm():
    """Try several candidate model names and return the first working LLM client.

    Optionally honor the `DEVLOOP_MODEL` env var to try a preferred model first.
    """
    candidates = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-pro",
    ]

    pref = os.getenv("DEVLOOP_MODEL")
    if pref:
        candidates.insert(0, pref)

    last_err = None
    for model_name in candidates:
        try:
            client = ChatGoogleGenerativeAI(model=model_name, temperature=0)
            return client
        except Exception as e:
            last_err = e
            continue

    print(f"⚠️ LLM Init Failed for all candidates: {last_err}")
    return None

llm = get_working_llm()

class DevState(TypedDict):
    objective: str; code_content: str; test_content: str; test_output: str
    security_report: str; status: str; iterations: int; logs: list

def clean_content(response):
    content = response.content
    if isinstance(content, list):
        content = "".join([part if isinstance(part, str) else part.get("text", "") for part in content])
    return str(content).replace("```python", "").replace("```", "").strip()

def run_security_scan(filename):
    try:
        cmd = ["bandit", "-r", filename, "-f", "txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return "Clear" if result.returncode == 0 else result.stdout
    except FileNotFoundError: return "⚠️ Bandit not found."

# --- NODES ---
def architect_node(state: DevState):
    if not llm: return {"logs": ["❌ No API Key found."]}
    log = "🏗️ [ARCHITECT] Designing unit tests (TDD)..."
    prompt = f"Write a pytest file for: '{state['objective']}'. Filename: test_solution.py. Import 'solution'. ONLY code."
    try:
        res = clean_content(llm.invoke([HumanMessage(content=prompt)]))
        write_file("test_solution.py", res)
        return {"test_content": res, "iterations": 0, "logs": [log, "✅ Tests Generated."]}
    except Exception as e: return {"logs": [f"❌ Error: {str(e)}"]}

def developer_node(state: DevState):
    i = state.get("iterations", 0) + 1
    log = f"👨‍💻 [DEVELOPER] Coding (Cycle {i})..."
    context = ""
    if state.get("test_output") and "failed" in state.get("test_output", "").lower():
        context += f"\nTEST FAILURES:\n{state['test_output']}"
    sec_rep = state.get("security_report", "")
    if sec_rep and "High" in sec_rep and "High: 0" not in sec_rep:
        context += f"\nSECURITY ISSUES:\n{sec_rep}"
    
    prompt = f"Fix code based on:\n{context}\nObjective: {state['objective']}\nONLY python code." if context else f"Write python code for: '{state['objective']}'. File: 'solution.py'. ONLY python code."
    
    try:
        res = clean_content(llm.invoke([HumanMessage(content=prompt)]))
        write_file("solution.py", res)
        return {"code_content": res, "iterations": i, "logs": [log]}
    except Exception as e: return {"logs": [f"❌ Error: {str(e)}"]}

def security_node(state: DevState):
    log = "🛡️ [SEC-OPS] Scanning..."
    report = run_security_scan("solution.py")
    # SMART FILTER: Ignore low severity subprocess warnings
    if "High: 0" in report and ("B404" in report or "B603" in report):
        log = "✅ [SEC-OPS] Subprocess usage verified safe."
        report = "Clear"
    return {"security_report": report, "logs": [log]}

def tester_node(state: DevState):
    log = "⚡ [TESTER] Running Tests..."
    result = run_test("solution.py", "test_solution.py")
    status = result.get('status', 'failed') if isinstance(result, dict) else "failed"
    output = result.get('output', 'Error') if isinstance(result, dict) else str(result)
    final_log = "✅ [SUCCESS] Tests Passed!" if status == 'success' else "❌ [FAIL] Tests Failed."
    return {"test_output": output, "status": status, "logs": [log, final_log]}

def router(state: DevState):
    sec = state.get("security_report", "")
    if state["status"] == "success" and ("Clear" in sec or "High: 0" in sec): return END
    if state["iterations"] > 10: return END
    return "developer"

workflow = StateGraph(DevState)
workflow.add_node("architect", architect_node)
workflow.add_node("developer", developer_node)
workflow.add_node("security", security_node)
workflow.add_node("tester", tester_node)
workflow.set_entry_point("architect")
workflow.add_edge("architect", "developer")
workflow.add_edge("developer", "security")
workflow.add_edge("security", "tester")
workflow.add_conditional_edges("tester", router, {END: END, "developer": "developer"})
agent_app = workflow.compile()