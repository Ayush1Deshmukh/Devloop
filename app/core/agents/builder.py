# "I built a state-machine based agent using LangGraph. If the generated code fails a compilation check or contains unsafe functions like eval(), the system triggers a conditional edge to route the state back to the LLM for a corrected iteration. It essentially performs a self-healing loop until the code is both functional and secure."
import json
import urllib.request
import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# Security: Pull from environment variable
API_KEY = os.getenv("GOOGLE_API_KEY")

class DevState(TypedDict):
    objective: str
    code_content: str
    test_output: str
    security_report: str
    status: str
    iterations: int
    logs: List[str]

def ask_ai(prompt: str):
    if not API_KEY:
        return "print('Error: API Key missing')"
    
    try:
        # Grounding to current stable Gemini models
        model = "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        
        # System instructions to enforce raw code output
        payload = {
            "contents": [{
                "parts": [{"text": f"SYSTEM: You are an expert Python coder. Return ONLY raw code without markdown blocks or explanations.\nUSER: {prompt}"}]
            }]
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read().decode())
            return res["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"# Error contacting AI Engine: {str(e)}"

def developer_node(state: DevState):
    iters = state.get("iterations", 0)
    
    if state.get("test_output") and "Error" in state["test_output"]:
        prompt = f"The previous code failed. Fix it.\nCODE:\n{state['code_content']}\nERROR:\n{state['test_output']}"
    else:
        prompt = f"Write a robust Python solution for: {state['objective']}"
    
    # Clean output in case LLM adds markdown wrappers
    code = ask_ai(prompt).replace("```python", "").replace("```", "").strip()
    
    return {
        "code_content": code, 
        "iterations": iters + 1, 
        "logs": state.get("logs", []) + [f"Iteration {iters+1}"]
    }

def security_node(state: DevState):
    unsafe_patterns = ["os.system", "eval(", "exec(", "subprocess.call", "shutil."]
    report = "Clear"
    for pattern in unsafe_patterns:
        if pattern in state["code_content"]:
            report = f"Unsafe function detected: {pattern}"
            break
    return {"security_report": report}

def tester_node(state: DevState):
    # If security check failed, force a retry regardless of syntax
    if state["security_report"] != "Clear":
        return {"status": "retry", "test_output": f"Security Violation: {state['security_report']}"}
        
    try:
        compile(state["code_content"], "solution.py", "exec")
        return {"status": "completed", "test_output": "Passed"}
    except Exception as e:
        # Max 3 attempts
        if state["iterations"] < 3:
            return {"status": "retry", "test_output": str(e)}
        return {"status": "failed", "test_output": str(e)}

def router(state: DevState):
    return "developer" if state["status"] == "retry" else END

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