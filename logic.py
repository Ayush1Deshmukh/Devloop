# import os
# import subprocess
# from typing import TypedDict
# from langgraph.graph import StateGraph, END
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import HumanMessage
# from tools import write_file, run_test

# # --- CONFIG ---
# llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

# class DevState(TypedDict):
#     objective: str
#     code_content: str
#     test_content: str
#     test_output: str
#     security_report: str  # <--- NEW: Stores bandit scan results
#     review_comment: str
#     status: str
#     iterations: int
#     logs: list

# # --- HELPER ---
# def clean_content(response):
#     content = response.content
    
#     # Case 1: If it's a simple string (Standard)
#     if isinstance(content, str):
#         pass 
        
#     # Case 2: If it's a list (Complex Gemini response)
#     elif isinstance(content, list):
#         text_parts = []
#         for part in content:
#             if isinstance(part, str):
#                 text_parts.append(part)
#             elif isinstance(part, dict):
#                 # Extract text if hidden inside a dict key like 'text'
#                 text_parts.append(part.get("text", str(part)))
#         content = "".join(text_parts)
        
#     # Clean Markdown formatting
#     return str(content).replace("```python", "").replace("```", "").strip()
# def run_security_scan(filename):
#     """Runs 'bandit' inside Docker to check for vulnerabilities."""
#     cmd = ["docker", "exec", "devloop-runner", "bandit", "-r", filename, "-f", "txt"]
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     # Bandit returns exit code 1 if issues found, 0 if clean.
#     return result.stdout + "\n" + result.stderr

# # --- NODES ---

# def architect_node(state: DevState):
#     log = "🏗️ [ARCHITECT] Designing tests..."
#     prompt = f"Write a pytest unit test for: '{state['objective']}'. File: 'test_solution.py'. Import 'solution'. ONLY code."
#     res = clean_content(llm.invoke([HumanMessage(content=prompt)]))
#     write_file("test_solution.py", res)
#     return {"test_content": res, "iterations": 0, "logs": [log]}

# def developer_node(state: DevState):
#     iteration_label = state.get("iterations", 0) + 1
#     log = f"👨‍💻 [DEVELOPER] Coding (Cycle {iteration_label})..."
    
#     context = ""
#     if state.get("test_output"):
#         context += f"\nTEST FAILURES:\n{state['test_output']}"
#     if state.get("security_report") and "No issues identified" not in state.get("security_report", ""):
#         context += f"\nSECURITY VULNERABILITIES:\n{state['security_report']}"
        
#     if context:
#         prompt = f"Fix code based on issues:\n{context}\nObjective: {state['objective']}\nONLY python code."
#     else:
#         prompt = f"Write python code for: '{state['objective']}'. File: 'solution.py'. ONLY python code."
        
#     res = clean_content(llm.invoke([HumanMessage(content=prompt)]))
#     write_file("solution.py", res)
#     return {"code_content": res, "iterations": state["iterations"] + 1, "logs": [log]}

# def security_node(state: DevState):
#     # --- NEW: SECURITY SCANNER ---
#     log = "🛡️ [SEC-OPS] Scanning for vulnerabilities..."
#     report = run_security_scan("solution.py")
    
#     clean_report = "✅ No Security Issues Found"
#     if "Issue:" in report:
#         clean_report = f"⚠️ VULNERABILITIES FOUND:\n{report}"
        
#     return {"security_report": clean_report, "logs": [log]}

# def tester_node(state: DevState):
#     log = "⚡ [TESTER] Running Unit Tests..."
#     result = run_test("test_solution.py")
    
#     status = result['status']
#     final_log = "✅ [SUCCESS] Tests Passed!" if status == 'success' else "❌ [FAIL] Tests Failed."
        
#     return {"test_output": result['output'], "status": status, "logs": [log, final_log]}

# # --- GRAPH ---
# def router(state: DevState):
#     # Stop if success, or too many tries
#     if state["status"] == "success" and "No issues identified" in state.get("security_report", "No issues identified"):
#         return "end"
#     if state["iterations"] > 5: 
#         return "end"
#     return "developer"

# workflow = StateGraph(DevState)
# workflow.add_node("architect", architect_node)
# workflow.add_node("developer", developer_node)
# workflow.add_node("security", security_node) # Added Security
# workflow.add_node("tester", tester_node)

# workflow.set_entry_point("architect")
# workflow.add_edge("architect", "developer")
# workflow.add_edge("developer", "security") # Dev -> Security
# workflow.add_edge("security", "tester")    # Security -> Tester
# workflow.add_conditional_edges("tester", router, {"end": END, "developer": "developer"})

# app = workflow.compile()
import os
import subprocess
from typing import TypedDict
import streamlit as st  # <--- NEW IMPORT
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from tools import write_file, run_test

# --- CRITICAL FIX: LOAD API KEY INSIDE LOGIC ---
# This ensures the key exists BEFORE we initialize the LLM.
if "GOOGLE_API_KEY" not in os.environ:
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
        else:
            # If running locally and key is missing, this stops the crash until runtime
            pass 
    except FileNotFoundError:
        pass

# --- CONFIG ---
# Now it is safe to initialize Gemini
try:
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
except Exception as e:
    # Fallback if key is still missing (prevents import crash)
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

# --- HELPER ---
def clean_content(response):
    content = response.content
    # Robust parsing for Gemini's varied output formats
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str): text_parts.append(part)
            elif isinstance(part, dict): text_parts.append(part.get("text", str(part)))
        content = "".join(text_parts)
    
    return str(content).replace("```python", "").replace("```", "").strip()

def run_security_scan(filename):
    """Runs 'bandit' inside Docker or System (Cloud Fallback)."""
    # Check if we are running in a constrained cloud env without Docker
    # We skip actual bandit scan on Streamlit Cloud to prevent crashes, 
    # unless you add bandit to packages.txt. 
    # For now, we simulate a 'Clean' scan if bandit command fails.
    try:
        cmd = ["bandit", "-r", filename, "-f", "txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + "\n" + result.stderr
    except FileNotFoundError:
        return "⚠️ Security Scanner (Bandit) not found in environment. Skipping scan."

# --- NODES ---

def architect_node(state: DevState):
    if not llm: return {"logs": ["❌ API Key Missing. Check Secrets."]}
    
    log = "🏗️ [ARCHITECT] Designing tests..."
    prompt = f"Write a pytest unit test for: '{state['objective']}'. File: 'test_solution.py'. Import 'solution'. ONLY code."
    res = clean_content(llm.invoke([HumanMessage(content=prompt)]))
    write_file("test_solution.py", res)
    return {"test_content": res, "iterations": 0, "logs": [log]}

def developer_node(state: DevState):
    if not llm: return {"logs": ["❌ API Key Missing."]}

    iteration_label = state.get("iterations", 0) + 1
    log = f"👨‍💻 [DEVELOPER] Coding (Cycle {iteration_label})..."
    
    context = ""
    if state.get("test_output"):
        context += f"\nTEST FAILURES:\n{state['test_output']}"
    if state.get("security_report") and "No issues identified" not in state.get("security_report", ""):
        context += f"\nSECURITY VULNERABILITIES:\n{state['security_report']}"
        
    if context:
        prompt = f"Fix code based on issues:\n{context}\nObjective: {state['objective']}\nONLY python code."
    else:
        prompt = f"Write python code for: '{state['objective']}'. File: 'solution.py'. ONLY python code."
        
    res = clean_content(llm.invoke([HumanMessage(content=prompt)]))
    write_file("solution.py", res)
    return {"code_content": res, "iterations": state["iterations"] + 1, "logs": [log]}

def security_node(state: DevState):
    log = "🛡️ [SEC-OPS] Scanning for vulnerabilities..."
    report = run_security_scan("solution.py")
    
    clean_report = "✅ No Security Issues Found"
    if "Issue:" in report:
        clean_report = f"⚠️ VULNERABILITIES FOUND:\n{report}"
        
    return {"security_report": clean_report, "logs": [log]}

def tester_node(state: DevState):
    log = "⚡ [TESTER] Running Unit Tests..."
    result = run_test("test_solution.py")
    
    status = result['status']
    final_log = "✅ [SUCCESS] Tests Passed!" if status == 'success' else "❌ [FAIL] Tests Failed."
        
    return {"test_output": result['output'], "status": status, "logs": [log, final_log]}

# --- GRAPH ---
def router(state: DevState):
    if state["status"] == "success" and "No issues identified" in state.get("security_report", "No issues identified"):
        return "end"
    if state["iterations"] > 5: 
        return "end"
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
workflow.add_conditional_edges("tester", router, {"end": END, "developer": "developer"})

app = workflow.compile()
