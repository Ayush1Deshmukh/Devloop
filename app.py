import streamlit as st
import os
import sys

# --- THE CRITICAL FIX: REVEAL THE 'app' FOLDER ---
# This adds the /app directory to Python's search path so it can find your modules
current_dir = os.path.dirname(__file__)
app_path = os.path.join(current_dir, 'app')
if app_path not in sys.path:
    sys.path.append(app_path)

# --- 1. SECRETS SETUP ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    pass

import streamlit.components.v1 as components
import time

# Now we can import these because of the sys.path.append fix
# If logic.py is in the same folder as app.py
try:
    from logic import agent_app as logic_app, write_file
except ImportError:
    # This handles the case if you eventually move it to the 'app' folder
    from app.logic import agent_app as logic_app, write_file

# --- 2. CONFIG ---
st.set_page_config(
    page_title="DevLoop Prime",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ... [KEEP ALL YOUR CSS AND HEADER CODE EXACTLY THE SAME] ...
# [Section 3, 4, 5, 6, and 7 remain unchanged]

# --- 8. EXECUTION LOGIC (BACKEND CONNECTION) ---
if st.session_state.get("running", False):
    
    # 1. Setup Input
    initial_code = ""
    if uploaded_file:
        initial_code = uploaded_file.read().decode("utf-8")
        # Ensure tools.write_file works in cloud (might need /tmp path)
        write_file("solution.py", initial_code)
    
    if not objective and not initial_code:
        st.warning("⚠️ Please provide an objective or file.")
        st.session_state.running = False
        st.stop()

    inputs = {
        "objective": objective if objective else "Refactor provided code",
        "code_content": initial_code,
        "test_content": "", 
        "test_output": "", 
        "status": "pending", 
        "iterations": 0, 
        "logs": []
    }

    # 2. Run Stream
    logs_history = []
    
    try:
        # Use .stream() from your LangGraph agent
        for event in logic_app.stream(inputs):
            for node_name, node_data in event.items():
                
                # A. Update Terminal
                if "logs" in node_data:
                    for log in node_data["logs"]:
                        ts = time.strftime("%H:%M:%S")
                        icon = "🔹"
                        if "ARCHITECT" in log: icon = "📐"
                        elif "DEVELOPER" in log: icon = "👨‍💻"
                        elif "TESTER" in log: icon = "🧪"
                        elif "SUCCESS" in log: icon = "✅"
                        elif "FAIL" in log: icon = "❌"
                        
                        entry = f"""
                        <div class="log-line">
                            <span style="color:#71717a; font-size:0.7rem; margin-right:8px;">{ts}</span>
                            <span>{icon} {log}</span>
                        </div>
                        """
                        logs_history.insert(0, entry)
                        
                        log_html = "".join(logs_history)
                        terminal_container.markdown(f"""
                        <div class="terminal">
                            <div class="terminal-header">
                                <div class="dot" style="background:#ef4444"></div>
                                <div class="dot" style="background:#eab308"></div>
                                <div class="dot" style="background:#22c55e"></div>
                            </div>
                            <div class="logs">{log_html}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.05)

                # B. Update UI Tabs
                if "code_content" in node_data:
                    with tabs[1]: st.code(node_data["code_content"], language="python", line_numbers=True)
                
                if "test_content" in node_data:
                    with tabs[2]: st.code(node_data["test_content"], language="python", line_numbers=True)

                if "security_report" in node_data:
                    with tabs[3]: 
                        st.info(node_data["security_report"])

        st.success("Sequence Completed Successfully")
        st.balloons()
        st.session_state.running = False
        
    except Exception as e:
        st.error(f"System Failure: {e}")
        st.session_state.running = False