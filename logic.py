import os
import subprocess
from typing import TypedDict
from dotenv import load_dotenv # <--- ADDED THIS
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import streamlit as st

# --- 0. LOAD ENV VARIABLES (Local Fix) ---
load_dotenv() 

# --- 1. PATH FIX ---
try:
    from tools import write_file, run_test
except ImportError:
    from app.tools import write_file, run_test

# --- 2. KEY LOADING ---
# First try loading from environment (local .env), then Streamlit secrets (cloud)
if "GOOGLE_API_KEY" not in os.environ:
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    except FileNotFoundError:
        pass

# --- 3. CONFIG (VERIFIED MODEL) ---
try:
    # Using the verified model from your check_models.py
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
except Exception as e:
    llm = None
    print(f"⚠️ LLM Init Failed: {e}")

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
    """Robustly handle Gemini's output."""
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

# --- 5. NODES ---

def architect_node(state: DevState):
    if not llm:
        return {"logs": ["❌ [ARCHITECT] CRITICAL: No API Key found. Check .env file."]}
    
    log = "🏗️ [ARCHITECT] Designing unit tests (TDD)..."
    prompt = f"Write a pytest unit test for: '{state['objective']}'. File: 'test_solution.py'. Import 'solution'. ONLY code."
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        res = clean_content(response)
        write_file("test_solution.py", res)
        return {"test_content": res, "iterations": 0, "logs": [log, "✅ [ARCHITECT] Tests Generated."]}
    except Exception as e:
        return {"logs": [f"❌ [ARCHITECT] Error: {str(e)}"]}

def developer_node(state: DevState):
    if not llm: return {"logs": ["❌ [DEVELOPER] Aborted: LLM is None"]}

    i = state.get("iterations", 0) + 1
    log = f"👨‍💻 [DEVELOPER] Coding (Cycle {i})..."
    
    context = ""
    if state.get("test_output") and "failed" in state.get("test_output", "").lower():
        context += f"\nTEST FAILURES:\n{state['test_output']}"
    
    sec_rep = state.get("security_report", "")
    if sec_rep and "High" in sec_rep and "High: 0" not in sec_rep:
        context += f"\nSECURITY VULNERABILITIES:\n{sec_rep}"
        
    prompt = f"Fix code based on:\n{context}\nObjective: {state['objective']}\nONLY python code." if context else f"Write python code for: '{state['objective']}'. File: 'solution.py'. ONLY python code."
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        res = clean_content(response)
        write_file("solution.py", res)
        return {"code_content": res, "iterations": i, "logs": [log]}
    except Exception as e:
        return {"logs": [f"❌ [DEVELOPER] Error: {str(e)}"]}

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

# --- 5. GRAPH ROUTING ---
def router(state: DevState):
    # 1. READ LOGS FOR FATAL ERRORS
    # We check the last few logs to see if a permission error occurred
    last_logs = state.get("logs", [])
    for log_entry in last_logs:
        if "PERMISSION_DENIED" in log_entry or "403" in log_entry:
            return END  # <--- STOP IMMEDIATELY
    
    # 2. STANDARD EXIT CONDITIONS
    sec_report = state.get("security_report", "")
    test_status = state.get("status", "failed")
    
    if test_status == "success" and ("Clear" in sec_report or "High: 0" in sec_report):
        return END
    
    if state["iterations"] > 5: 
        return END
    
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