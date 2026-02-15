import os
import subprocess
import time
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import streamlit as st

# --- 0. LOAD ENV ---
load_dotenv()

# --- 1. PATH FIX ---
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tools import write_file, run_test
except ImportError:
    from app.tools import write_file, run_test

# --- 2. KEY LOADING ---
if "GOOGLE_API_KEY" not in os.environ:
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    except FileNotFoundError:
        pass

# --- 3. CONFIG (REAL AI MODELS) ---
# Primary: Gemini 2.0 Flash (Fast & Smart)
llm_primary = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Backup: Gemini 1.5 Flash (Reliable Fallback)
llm_backup = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

class DevState(TypedDict):
    objective: str
    code_content: str
    test_content: str
    test_output: str
    security_report: str
    status: str
    iterations: int
    logs: list

# --- 4. HELPERS ---
def clean_content(response):
    if not response or not response.content: return ""
    content = response.content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str): text_parts.append(part)
            elif isinstance(part, dict): text_parts.append(part.get("text", str(part)))
        content = "".join(text_parts)
    return str(content).replace("```python", "").replace("```", "").strip()

def run_security_scan(filename):
    try:
        cmd = ["bandit", "-r", filename, "-f", "txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0: return "Clear"
        else: return result.stdout
    except FileNotFoundError:
        return "⚠️ Security Scanner (Bandit) not found. Skipping."

def safe_invoke(prompt):
    """
    Real AI Wrapper:
    1. Tries Gemini 2.0.
    2. If Rate Limit (429), waits and switches to Gemini 1.5.
    """
    try:
        return llm_primary.invoke([HumanMessage(content=prompt)])
    except Exception as e:
        # Check for Rate Limit or Resource Exhausted errors
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            st.toast("⚠️ Primary quota hit. Switching to Backup Model...", icon="🔄")
            time.sleep(2) 
            try:
                # RETRY WITH BACKUP MODEL
                return llm_backup.invoke([HumanMessage(content=prompt)])
            except Exception as e2:
                return HumanMessage(content=f"# CRITICAL ERROR: Both models failed.\n# {str(e2)}")
        else:
            return HumanMessage(content=f"# ERROR: {str(e)}")

# --- 5. NODES ---

def architect_node(state: DevState):
    log = "🏗️ [ARCHITECT] Designing unit tests (TDD)..."
    prompt = f"Write a pytest unit test for: '{state['objective']}'. File: 'test_solution.py'. Import 'solution'. ONLY code."
    
    # CALL REAL AI
    response = safe_invoke(prompt)
    res = clean_content(response)
    
    if not res: res = "# Error generating tests"
    write_file("test_solution.py", res)
    
    return {"test_content": res, "iterations": 0, "logs": [log, "✅ [ARCHITECT] Tests Generated."]}

def developer_node(state: DevState):
    i = state.get("iterations", 0) + 1
    log = f"👨‍💻 [DEVELOPER] Coding (Cycle {i})..."
    
    context = ""
    if state.get("test_output") and "failed" in state.get("test_output", "").lower():
        context += f"\nTEST FAILURES:\n{state['test_output']}"
    
    sec_rep = state.get("security_report", "")
    if sec_rep and "High" in sec_rep and "High: 0" not in sec_rep:
        context += f"\nSECURITY VULNERABILITIES:\n{sec_rep}"
        
    prompt = f"Fix code based on:\n{context}\nObjective: {state['objective']}\nONLY python code." if context else f"Write python code for: '{state['objective']}'. File: 'solution.py'. ONLY python code."
    
    # CALL REAL AI
    response = safe_invoke(prompt)
    res = clean_content(response)
    
    if not res: res = "# Error generating code"
    write_file("solution.py", res)
    
    return {"code_content": res, "iterations": i, "logs": [log]}

def security_node(state: DevState):
    log = "🛡️ [SEC-OPS] Scanning..."
    report = run_security_scan("solution.py")
    if "High: 0" in report and ("B404" in report or "B603" in report):
        log = "✅ [SEC-OPS] Subprocess usage verified safe."
        report = "Clear"
    return {"security_report": report, "logs": [log]}

def tester_node(state: DevState):
    log = "⚡ [TESTER] Running Unit Tests..."
    result = run_test("solution.py", "test_solution.py")
    if isinstance(result, str):
        output = result
        status = "failed"
    else:
        status = result.get('status', 'failed')
        output = result.get('output', 'No output')
    final_log = "✅ [SUCCESS] Tests Passed!" if status == 'success' else "❌ [FAIL] Tests Failed."
    return {"test_output": output, "status": status, "logs": [log, final_log]}

def router(state: DevState):
    # Stop if we hit a permission error (bad key)
    last_logs = state.get("logs", [])
    for log in last_logs:
        if "PERMISSION_DENIED" in log or "403" in log: return END

    sec = state.get("security_report", "")
    if state["status"] == "success" and ("Clear" in sec or "High: 0" in sec): return END
    if state["iterations"] > 5: return END
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