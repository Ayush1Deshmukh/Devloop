import streamlit as st
import os
import sys
import time
import streamlit.components.v1 as components

# --- 1. CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="DevLoop Prime",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SAFE IMPORT LOGIC (The "White Screen" Fix) ---
try:
    # Add current directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Try imports with fallbacks
    try:
        from logic import agent_app as logic_app
        from tools import write_file
    except ImportError:
        from app.logic import agent_app as logic_app
        from app.tools import write_file
        
except Exception as e:
    st.error(f"⚠️ Critical System Initialization Error: {e}")
    st.stop()

# --- 3. JAVASCRIPT: MOUSE TRACKING ---
components.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('mousemove', function(e) {
        const x = e.clientX;
        const y = e.clientY;
        doc.documentElement.style.setProperty('--x', x + 'px');
        doc.documentElement.style.setProperty('--y', y + 'px');
    });
    </script>
    """,
    height=0, width=0
)

# --- 4. CSS: CYBERPUNK THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --primary: #6366f1;
        --secondary: #ec4899;
        --bg-deep: #09090b;
        --glass: rgba(24, 24, 27, 0.7);
        --border: rgba(255, 255, 255, 0.08);
    }

    .stApp { background-color: var(--bg-deep); font-family: 'Inter', sans-serif; }
    
    /* Background Grid & Spotlight */
    .stApp::before {
        content: ""; position: fixed; inset: 0;
        background-image: radial-gradient(#27272a 1px, transparent 1px);
        background-size: 40px 40px; opacity: 0.2; pointer-events: none;
    }
    .stApp::after {
        content: ""; position: fixed; inset: 0;
        background: radial-gradient(600px circle at var(--x) var(--y), rgba(99, 102, 241, 0.08), transparent 40%);
        pointer-events: none; z-index: 0;
    }

    /* Glass Cards */
    .glass-card {
        background: var(--glass);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px; transition: transform 0.2s;
    }
    .glass-card:hover { border-color: rgba(99, 102, 241, 0.4); }

    /* Navbar */
    .navbar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 16px 24px; margin-bottom: 30px;
    }
    
    /* Terminal Logs */
    .terminal {
        background: #000000; border: 1px solid #333; border-radius: 8px;
        font-family: 'JetBrains Mono', monospace; height: 400px;
        padding: 12px; overflow-y: auto; color: #4ade80; font-size: 0.85rem;
        display: flex; flex-direction: column-reverse;
    }
    .log-line { border-left: 2px solid #333; padding-left: 10px; margin-bottom: 4px; }
    
    /* Custom Buttons */
    div[data-testid="stButton"] button {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white; border: none; font-weight: 600; padding: 12px 24px;
        width: 100%; transition: all 0.3s;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-2px); box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
    }
    
    /* Diagram & Info Text */
    .info-text { color: #a1a1aa; font-size: 0.9rem; line-height: 1.6; }
    .arch-diagram {
        background: #18181b; padding: 20px; border-radius: 8px; 
        border: 1px dashed #3f3f46; margin-top: 10px;
        font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #e4e4e7;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. UI: HEADER & STATS ---
st.markdown("""
<div class="glass-card navbar">
    <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:28px;">⚡</span>
        <div>
            <div style="font-weight:700; font-size:1.2rem; letter-spacing:-0.5px; color:white;">DEVLOOP PRIME</div>
            <div style="font-size:0.8rem; color:#a1a1aa;">Autonomous DevSecOps Architect</div>
        </div>
    </div>
    <div style="font-family:'JetBrains Mono'; font-size:0.75rem; background:rgba(255,255,255,0.05); padding:6px 12px; border-radius:6px; color:#4ade80;">
        ● SYSTEM ONLINE
    </div>
</div>
""", unsafe_allow_html=True)

# --- 6. ARCHITECTURE EXPLAINER (Essential for Demo) ---
with st.expander("🏗️ How It Works: Polyglot Microservices Architecture"):
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        ### 🔄 The Self-Healing Loop
        DevLoop doesn't just write code; it **fixes itself**.
        1.  **Architect Agent:** Analyzes your request and writes `pytest` unit tests (TDD).
        2.  **Developer Agent:** Writes Python code to pass those tests.
        3.  **SecOps Agent:** Scans the code using `Bandit` for security flaws.
        4.  **Sandbox:** Executes the code in an isolated environment.
        
        *If any step fails, the error stack trace is fed back to the Developer for retry.*
        """)
    with c2:
        st.markdown("""
        ### 🛠️ System Stack
        <div class="arch-diagram">
        USER REQUEST ➜ [☕ Spring Boot Gateway]
                            ⬇️ (REST API)
                       [🐍 FastAPI AI Engine]
                            ⬇️ (LangGraph)
                       [🤖 Multi-Agent System]
                            🔄 (Loop)
                       [🐳 Docker/Hybrid Sandbox]
        </div>
        """, unsafe_allow_html=True)

# --- 7. MAIN WORKSPACE ---
col_input, col_logs = st.columns([1, 1.5])

with col_input:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("💠 Mission Control")
    
    objective = st.text_area("Task Objective", height=120, placeholder="E.g., Write a secure function to validate email addresses using Regex...")
    
    uploaded_file = st.file_uploader("Inject Source Code (Optional)", type=["py"]) 
    
    if st.button("INITIALIZE SEQUENCE 🚀"):
        if not objective and not uploaded_file:
            st.warning("⚠️ Please provide an objective or upload a file.")
        else:
            st.session_state.running = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_logs:
    st.markdown('<div class="glass-card" style="min-height:500px;">', unsafe_allow_html=True)
    st.subheader("📟 Neural Console")
    
    tabs = st.tabs(["Execution Log", "Source Code", "Tests", "Security Report"]) 
    
    with tabs[0]:
        terminal_container = st.empty()
        terminal_container.markdown('<div class="terminal"><div style="color:#666">Waiting for command...</div></div>', unsafe_allow_html=True)
    
    with tabs[1]:
        code_container = st.empty()
    
    with tabs[2]:
        test_container = st.empty()
        
    with tabs[3]:
        sec_container = st.empty()
        
    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. EXECUTION ENGINE ---
if st.session_state.get("running", False):
    
    # Prepare Input
    initial_code = ""
    if uploaded_file:
        initial_code = uploaded_file.read().decode("utf-8")
        write_file("solution.py", initial_code)
        
    inputs = {
        "objective": objective if objective else "Refactor provided code",
        "code_content": initial_code,
        "test_content": "", "test_output": "", 
        "security_report": "", "status": "pending", 
        "iterations": 0, "logs": []
    }

    logs_history = []
    
    try:
        # Stream the LangGraph workflow
        for event in logic_app.stream(inputs):
            for node_name, node_data in event.items():
                
                # Update Terminal
                if "logs" in node_data:
                    for log in node_data["logs"]:
                        ts = time.strftime("%H:%M:%S")
                        icon = "🔹"
                        if "ARCHITECT" in log: icon = "📐"
                        elif "DEVELOPER" in log: icon = "👨‍💻"
                        elif "TESTER" in log: icon = "🧪"
                        elif "SEC" in log: icon = "🛡️"
                        elif "SUCCESS" in log: icon = "✅"
                        
                        entry = f"""<div class="log-line"><span style="color:#71717a; margin-right:8px;">{ts}</span> {icon} {log}</div>"""
                        logs_history.insert(0, entry)
                        
                        terminal_container.markdown(f"""
                        <div class="terminal">
                            {"".join(logs_history)}
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.05) # Visual effect

                # Update Tabs
                if "code_content" in node_data:
                    code_container.code(node_data["code_content"], language="python", line_numbers=True)
                
                if "test_content" in node_data:
                    test_container.code(node_data["test_content"], language="python", line_numbers=True)
                    
                if "security_report" in node_data:
                    report = node_data["security_report"]
                    if "Clear" in report:
                        sec_container.success("✅ No Vulnerabilities Detected (Bandit Scan Passed)")
                    else:
                        sec_container.error(f"❌ Security Issues Found:\n{report}")

        st.success("✨ Autonomous Sequence Complete")
        st.balloons()
        st.session_state.running = False

    except Exception as e:
        st.error(f"❌ Execution Failure: {e}")
        st.session_state.running = False
