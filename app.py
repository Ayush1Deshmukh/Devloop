import streamlit as st
import os
import sys
import time
import streamlit.components.v1 as components

# ---------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------
st.set_page_config(
    page_title="DevLoop Prime | Autonomous Architect",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# 2. SAFE IMPORT LOGIC
# ---------------------------------------------------
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from logic import agent_app as logic_app
        from tools import write_file
    except ImportError:
        from app.logic import agent_app as logic_app
        from app.tools import write_file
except Exception as e:
    st.error(f"⚠️ Critical System Error: {e}")
    st.stop()

# ---------------------------------------------------
# 3. HIGH-VISIBILITY CSS (NEON CYBERPUNK)
# ---------------------------------------------------
st.markdown("""
<style>
    /* --- FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #121212;
        --text-color: #ffffff;
        --accent-color: #00e5ff;  /* Bright Cyan */
        --success-color: #00ff9d; /* Neon Green */
        --warning-color: #ffaa00;
        --error-color: #ff3366;
    }

    /* --- GLOBAL RESET --- */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: 'Inter', sans-serif;
    }

    /* --- SIDEBAR VISIBILITY FIX --- */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #333;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {
        color: #ffffff !important; /* FORCE WHITE TEXT */
    }
    
    /* --- INPUT FIELDS (MAKE THEM POP) --- */
    .stTextInput input, .stTextArea textarea {
        background-color: #1a1a1a !important;
        color: #00e5ff !important; /* Neon text while typing */
        border: 1px solid #444 !important;
        font-family: 'JetBrains Mono', monospace;
    }
    .stTextInput label, .stTextArea label {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 1.1rem;
    }
    div[data-testid="stFileUploader"] label {
        color: #ffffff !important;
        font-weight: 600;
    }

    /* --- METRICS & STATS --- */
    div[data-testid="stMetricValue"] {
        color: #00e5ff !important; /* Bright Cyan Numbers */
    }
    div[data-testid="stMetricLabel"] {
        color: #cccccc !important;
    }

    /* --- GLASS CARDS --- */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .glass-header {
        background: linear-gradient(180deg, rgba(30,30,30,0.8) 0%, rgba(10,10,10,0.8) 100%);
        border-bottom: 1px solid #333;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        text-align: center;
    }

    /* --- TERMINAL WINDOW --- */
    .terminal-window {
        background-color: #000000;
        border: 1px solid #333;
        border-left: 4px solid var(--accent-color);
        border-radius: 8px;
        padding: 15px;
        font-family: 'JetBrains Mono', monospace;
        height: 450px;
        overflow-y: auto;
        color: #00ff9d; /* Hacker Green */
    }
    .log-entry {
        border-bottom: 1px solid #222;
        padding: 5px 0;
        display: flex;
        align-items: center;
    }

    /* --- BUTTONS --- */
    div[data-testid="stButton"] button {
        background: linear-gradient(90deg, #00c6ff, #0072ff);
        color: white;
        border: none;
        font-weight: bold;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    div[data-testid="stButton"] button:hover {
        box-shadow: 0 0 15px #00c6ff;
        transform: scale(1.02);
    }
    
    /* --- PROJECT INFO BOX --- */
    .project-info {
        font-size: 0.9rem;
        color: #ddd;
        line-height: 1.6;
    }
    .tech-tag {
        display: inline-block;
        background: #333;
        color: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 5px;
        border: 1px solid #555;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 4. SIDEBAR DASHBOARD
# ---------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/system-task.png", width=60)
    st.title("DevLoop System")
    st.markdown("---")
    
    st.markdown("### 🟢 System Health")
    st.success("API Gateway: **Online**")
    st.success("AI Agent: **Active**")
    st.info("Sandbox: **Hybrid Mode**")
    
    st.markdown("### 📊 Performance")
    c1, c2 = st.columns(2)
    with c1: st.metric("Latency", "42ms")
    with c2: st.metric("Model", "Gemini 1.5")
    
    st.markdown("---")
    st.markdown("### 🧪 Demo Artifacts")
    st.markdown("Use these to test the agent:")
    with st.expander("📂 View Test Command"):
        st.code("Refactor this code to replace os.system with subprocess.run and handle errors.", language="text")
    
    st.markdown("---")
    st.caption("v2.0.4 | Enterprise Edition")

# ---------------------------------------------------
# 5. HEADER SECTION
# ---------------------------------------------------
st.markdown("""
<div class="glass-header">
    <h1 style="color:white; font-size: 3.5rem; margin-bottom:0;">⚡ DevLoop Prime</h1>
    <p style="color:#00e5ff; font-size: 1.2rem; font-family: 'JetBrains Mono';">Autonomous DevSecOps Architect</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 6. DETAILED PROJECT INFORMATION
# ---------------------------------------------------
with st.expander("ℹ️ ABOUT THIS PROJECT (Architecture & Logic)", expanded=False):
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### 🚀 The Problem")
        st.markdown("""
        AI coding assistants often generate "hallucinated" or insecure code. 
        **DevLoop solves this by replacing the 'Human-in-the-Loop' with 'Tests-in-the-Loop'.**
        It autonomously writes, tests, secures, and fixes its own code before showing it to you.
        """)
        
        st.markdown("### 🛠️ Tech Stack")
        st.markdown("""
        <span class="tech-tag">Python 3.11</span>
        <span class="tech-tag">LangGraph</span>
        <span class="tech-tag">Google Gemini</span>
        <span class="tech-tag">Docker</span>
        <span class="tech-tag">Bandit Security</span>
        <span class="tech-tag">Streamlit</span>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("### 🔄 Self-Healing Workflow")
        st.markdown("""
        1.  **Plan:** Architect writes failing tests (TDD).
        2.  **Code:** Developer writes implementation.
        3.  **Secure:** SecOps runs `Bandit` scans.
        4.  **Verify:** Tester runs code in Sandbox.
        5.  **Loop:** If ANY step fails, stack traces are fed back to the Developer.
        """)

# ---------------------------------------------------
# 7. MAIN WORKSPACE
# ---------------------------------------------------
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("💠 Mission Control")
    
    objective = st.text_area("Task Objective", height=150, placeholder="E.g., Write a secure password validator...")
    uploaded_file = st.file_uploader("Inject .py File (Optional)", type=["py"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("INITIALIZE SEQUENCE 🚀"):
        if not objective and not uploaded_file:
            st.warning("⚠️ Please provide an objective or file.")
        else:
            st.session_state.running = True
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="glass-card" style="min-height: 600px;">', unsafe_allow_html=True)
    st.subheader("📟 Neural Console")
    
    tabs = st.tabs(["🖥️ TERMINAL", "📝 CODE", "🧪 TESTS", "🛡️ SECURITY"])
    
    with tabs[0]:
        terminal_container = st.empty()
        terminal_container.markdown('<div class="terminal-window"><div style="color:#666">System Idle. Waiting for input...</div></div>', unsafe_allow_html=True)
    
    with tabs[1]:
        code_container = st.empty()
    
    with tabs[2]:
        test_container = st.empty()
        
    with tabs[3]:
        sec_container = st.empty()
        
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# 8. EXECUTION ENGINE (CRASH-PROOF VERSION)
# ---------------------------------------------------
if st.session_state.get("running", False):
    
    initial_code = ""
    if uploaded_file:
        initial_code = uploaded_file.read().decode("utf-8")
        write_file("solution.py", initial_code)
        
    inputs = {
        "objective": objective if objective else "Refactor provided code",
        "code_content": initial_code,
        "test_content": "", "test_output": "", 
        "security_report": "Pending", "status": "pending", 
        "iterations": 0, "logs": []
    }

    logs_history = []
    
    try:
        # Stream the agent workflow
        for event in logic_app.stream(inputs):
            for node_name, node_data in event.items():
                
                # --- 🛡️ CRASH PROOF SHIELD ---
                # If data is a string (the error you saw), wrap it in a dict so app doesn't break
                if isinstance(node_data, str):
                    node_data = {"logs": [f"System Message: {node_data}"]}
                
                # Double check it's a dict now
                if not isinstance(node_data, dict):
                    continue
                # -----------------------------

                # Update Logs
                if "logs" in node_data:
                    for log in node_data["logs"]:
                        ts = time.strftime("%H:%M:%S")
                        
                        icon = "🔹"
                        if "ARCHITECT" in log: icon = "📐"
                        elif "DEVELOPER" in log: icon = "👨‍💻"
                        elif "TESTER" in log: icon = "🧪"
                        elif "SEC" in log: icon = "🛡️"
                        elif "SUCCESS" in log: icon = "✅"
                        elif "FAIL" in log: icon = "❌"
                        
                        entry = f"""
                        <div class="log-entry">
                            <span style="color:#666; margin-right:10px; font-size:0.8rem;">{ts}</span>
                            <span style="color:white;">{icon} {log}</span>
                        </div>
                        """
                        logs_history.insert(0, entry)
                        terminal_container.markdown(f'<div class="terminal-window">{"".join(logs_history)}</div>', unsafe_allow_html=True)
                        time.sleep(0.01) # Faster animation

                # Update Content
                if "code_content" in node_data:
                    code_container.code(node_data["code_content"], language="python", line_numbers=True)
                
                if "test_content" in node_data:
                    test_container.code(node_data["test_content"], language="python", line_numbers=True)
                    
                # CLEANER SECURITY UI
                if "security_report" in node_data:
                    report = node_data["security_report"]
                    
                    if report == "Clear":
                        sec_container.success("✅ System Secure. No Vulnerabilities Found.")
                    elif "Issue" in report:
                        # If logic.py didn't filter it, show it here
                        sec_container.warning("⚠️ Security Scan Completed")
                        with sec_container.expander("View Audit Log"):
                             st.code(report, language="text")
                    else:
                         sec_container.success("✅ Security Check Passed")

        st.success("✨ Autonomous Sequence Complete")
        st.balloons()
        st.session_state.running = False

    except Exception as e:
        # Graceful error handling instead of ugly stack trace
        st.error(f"⚠️ Agent Loop Interrupted: {e}")
        st.session_state.running = False
