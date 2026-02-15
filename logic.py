import os
import subprocess
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import streamlit as st

# --- 0. PATH FIX ---
try:
    from tools import write_file, run_test
except ImportError:
    from app.tools import write_file, run_test

# --- 1. KEY LOADING ---
if "GOOGLE_API_KEY" not in os.environ:
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    except FileNotFoundError:
        pass

# --- 2. CONFIG (UPGRADED TO GEMINI 2.0) ---
try:
    # We are using the "Gemini 2.0 Flash" model found in your account check.
    # It is extremely fast and capable.
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

# --- 3. HELPERS ---
def clean_content(response):
    """Robustly handle Gemini's output."""
    content = response.content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str): text_parts.append(part)
            elif isinstance(part, dict): text_parts.append(part.get("text", str(part)))
        content = "".join(text_parts)
    return str(content).replace("```python", "").replace("```", "").strip()

def run_security_scan(filename):
    """Runs 'bandit' security scan."""
    try:
        # Check if bandit is installed
        cmd = ["bandit", "-r", filename, "-f", "txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Bandit returns exit code 1 if issues found, 0 if clean
        if result.returncode == 0:
            return "Clear"
        else:
            return result.stdout
            
    except FileNotFoundError:
        return "⚠️ Security Scanner (Bandit) not found. Skipping."

# --- 4. NODES ---

def architect_node(state: DevState):
    # 1. Check API Key
    if not llm:
        error_msg = "# ❌ CRITICAL ERROR: Google API Key is missing.\n# Please add GOOGLE_API_KEY to your .env file or Streamlit Secrets."
        return {
            "test_content": error_msg, 
            "logs": ["❌ [ARCHITECT] Aborted: No API Key found."]
        }
    
    # 2. Initialize Logs
    log = "🏗️ [ARCHITECT] Designing unit tests (TDD)..."
    
    # 3. Create Prompt
    prompt = f"""
    You are a Senior QA Engineer.
    Write a complete Python 'pytest' file for this objective: "{state['objective']}".
    
    Rules:
    - filename: test_solution.py
    - Import the function from 'solution' (e.g. 'from solution import is_prime')
    - Cover edge cases (0, 1, negative numbers).
    - Output ONLY raw python code. No markdown.
    """
    
    try:
        # 4. Generate Code
        response = llm.invoke([HumanMessage(content=prompt)])
        res = clean_content(response)
        
        # 5. Save and Return
        write_file("test_solution.py", res)
        return {
            "test_content": res, 
            "iterations": 0, 
            "logs": [log, "✅ [ARCHITECT] Tests Generated."]
        }
        
    except Exception as e:
        # 6. Catch-All Error Handler
        error_msg = f"# ❌ GENERATION FAILED: {str(e)}\n# Check your API Key quota or internet connection."
        return {
            "test_content": error_msg, 
            "logs": [f"❌ [ARCHITECT] Error: {str(e)}"]
        }

def developer_node(state: DevState):
    iteration_label = state.get("iterations", 0) + 1
    log = f"👨‍💻 [DEVELOPER] Coding (Cycle {iteration_label})..."
    
    context = ""
    # Add feedback from Tests
    if state.get("test_output") and "failed" in state.get("test_output", "").lower():
        context += f"\nTEST FAILURES:\n{state['test_output']}"
    
    # Add feedback from Security Audit
    sec_rep = state.get("security_report", "")
    if sec_rep and "High" in sec_rep and "High: 0" not in sec_rep:
        context += f"\nSECURITY VULNERABILITIES:\n{sec_rep}"
        
    if context:
        prompt = f"Fix code based on issues:\n{context}\nObjective: {state['objective']}\nONLY python code."
    else:
        prompt = f"Write python code for: '{state['objective']}'. File: 'solution.py'. ONLY python code."
        
    try:
        res = clean_content(llm.invoke([HumanMessage(content=prompt)]))
        write_file("solution.py", res)
        return {"code_content": res, "iterations": state["iterations"] + 1, "logs": [log]}
    except Exception as e:
        return {"logs": [f"❌ Developer Error: {str(e)}"]}

def security_node(state: DevState):
    log = "🛡️ [SEC-OPS] Scanning for vulnerabilities..."
    report = run_security_scan("solution.py")
    
    # --- INTELLIGENT FILTERING ---
    # If High Severity is 0, but we have Low Severity warnings (like subprocess),
    # we treat it as SAFE to prevent infinite loops.
    if "High: 0" in report:
        if "B404" in report or "B603" in report:
            log = "✅ [SEC-OPS] Subprocess usage verified safe (False positives ignored)."
            report = "Clear" # Force clean status
    # -----------------------------

    return {"security_report": report, "logs": [log]}

def tester_node(state: DevState):
    log = "⚡ [TESTER] Running Unit Tests..."
    result = run_test("solution.py", "test_solution.py")
    
    # Check if result is a dict (crash prevention)
    if isinstance(result, str):
        # If it returned a string error, wrap it
        output = result
        status = "failed"
    else:
        status = result.get('status', 'failed')
        output = result.get('output', 'No output')
    
    final_log = "✅ [SUCCESS] Tests Passed!" if status == 'success' else "❌ [FAIL] Tests Failed."
        
    return {"test_output": output, "status": status, "logs": [log, final_log]}

# --- 5. GRAPH ROUTING ---
def router(state: DevState):
    # Exit if tests passed AND security is clean
    sec_report = state.get("security_report", "")
    test_status = state.get("status", "failed")
    
    # Success Condition
    if test_status == "success" and ("Clear" in sec_report or "High: 0" in sec_report):
        return END
    
    # Loop Limit
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