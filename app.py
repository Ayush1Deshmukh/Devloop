import streamlit as st
import os
import sys
import time
import base64

# ---------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------
st.set_page_config(
    page_title="DevLoop Prime | Autonomous Architect",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # Start with full screen focus
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
# 3. ADVANCED CSS & ANIMATIONS
# ---------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #111111;
        --accent-blue: #00f3ff;
        --accent-green: #00ff9d;
        --accent-red: #ff0055;
        --text-primary: #ffffff;
        --text-secondary: #888888;
    }

    /* GLOBAL THEME */
    .stApp { background-color: var(--bg-color); font-family: 'Inter', sans-serif; }
    
    /* INPUTS */
    .stTextInput input, .stTextArea textarea {
        background-color: #0a0a0a !important; 
        color: var(--accent-blue) !important;
        border: 1px solid #333 !important; 
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);
    }

    /* GLASS CARDS */
    .glass-card {
        background: rgba(20, 20, 20, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .glass-card:hover { border-color: rgba(255, 255, 255, 0.2); }

    /* NEON HEADER */
    .neon-header {
        text-align: center;
        padding: 40px 0;
        background: radial-gradient(circle at center, rgba(0, 243, 255, 0.1) 0%, transparent 70%);
    }
    .neon-title {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #fff, var(--accent-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
        margin: 0;
    }

    /* TERMINAL WINDOW */
    .terminal-window {
        background-color: #000;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        font-family: 'JetBrains Mono', monospace;
        height: 400px;
        overflow-y: auto;
        color: var(--accent-green);
        box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8);
        position: relative;
    }
    .terminal-window::before {
        content: "root@devloop:~# ./execute_sequence.sh";
        display: block;
        color: #555;
        border-bottom: 1px solid #222;
        padding-bottom: 10px;
        margin-bottom: 10px;
        font-size: 0.8rem;
    }
    .log-entry { 
        padding: 4px 0; 
        border-bottom: 1px solid #111;
        animation: fadeIn 0.3s ease-in;
    }
    
    /* ANIMATIONS */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse-glow { 0% { box-shadow: 0 0 0 0 rgba(0, 243, 255, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(0, 243, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 243, 255, 0); } }

    /* WORKFLOW VISUALIZER */
    .workflow-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        margin-bottom: 20px;
        position: relative;
    }
    .workflow-line {
        position: absolute;
        top: 50%;
        left: 40px;
        right: 40px;
        height: 2px;
        background: #333;
        z-index: 0;
    }
    .node-step {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #111;
        border: 2px solid #444;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        z-index: 1;
        transition: all 0.3s ease;
        position: relative;
    }
    .node-active {
        border-color: var(--accent-blue);
        background: rgba(0, 243, 255, 0.1);
        color: var(--accent-blue);
        box-shadow: 0 0 15px var(--accent-blue);
        animation: pulse-glow 2s infinite;
    }
    .node-success {
        border-color: var(--accent-green);
        background: rgba(0, 255, 157, 0.1);
        color: var(--accent-green);
    }
    .node-label {
        position: absolute;
        bottom: -25px;
        font-size: 10px;
        color: #666;
        width: 100px;
        text-align: center;
        font-weight: bold;
        text-transform: uppercase;
    }
    .node-active .node-label { color: var(--accent-blue); }

    /* BUTTONS */
    div[data-testid="stButton"] button {
        width: 100%;
        background: linear-gradient(90deg, var(--accent-blue), #0072ff);
        color: white;
        border: none;
        padding: 1rem;
        font-size: 1.1rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    div[data-testid="stButton"] button:hover {
        box-shadow: 0 0 30px var(--accent-blue);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 4. HELPER FUNCTIONS FOR UI
# ---------------------------------------------------
def render_workflow(active_node):
    """Renders the progress bar with the active step highlighted."""
    steps = [
        {"id": "architect", "icon": "📐", "label": "PLAN"},
        {"id": "developer", "icon": "👨‍💻", "label": "CODE"},
        {"id": "security", "icon": "🛡️", "label": "SECURE"},
        {"id": "tester", "icon": "⚡", "label": "TEST"}
    ]
    
    html = '<div class="workflow-container"><div class="workflow-line"></div>'
    
    for step in steps:
        status_class = ""
        if active_node == step["id"]:
            status_class = "node-active"
        # Simple logic: If we are at "security", "architect" and "developer" are effectively 'done' (success)
        # For simplicity in this loop, we just highlight the active one.
        elif active_node == "done":
             status_class = "node-success"
            
        html += f"""
        <div class="node-step {status_class}">
            {step['icon']}
            <div class="node-label">{step['label']}</div>
        </div>
        """
    html += "</div>"
    return html

# ---------------------------------------------------
# 5. HEADER SECTION
# ---------------------------------------------------
st.markdown("""
<div class="neon-header">
    <div style="font-family: 'JetBrains Mono'; color: var(--accent-blue); margin-bottom: 10px;">SYSTEM: ONLINE</div>
    <h1 class="neon-title">DEVLOOP PRIME</h1>
    <p style="color: #888; font-size: 1.1rem; margin-top: 10px;">Autonomous DevSecOps Intelligence Engine</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 6. MAIN WORKSPACE
# ---------------------------------------------------
col_left, col_right = st.columns([1, 1.8])

with col_left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("💠 Mission Parameters")
    
    # Preset Objectives for fast Demo
    presets = st.selectbox("Quick Load Objective:", [
        "Custom...",
        "Write a secure login function with SQL injection protection",
        "Create a REST API endpoint for user registration",
        "Build a multi-threaded port scanner"
    ])
    
    if presets != "Custom...":
        default_text = presets
    else:
        default_text = ""

    objective = st.text_area("Operational Objective", value=default_text, height=120, placeholder="Describe the software module to build...")
    uploaded_file = st.file_uploader("Inject Source Code (Optional)", type=["py"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 INITIALIZE SEQUENCE"):
        if not objective and not uploaded_file:
            st.warning("⚠️ Protocol Halted: Missing Objective.")
        else:
            st.session_state.running = True
            st.session_state.logs = []
            st.session_state.active_node = "architect"
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 📊 Live Telemetry")
    m1, m2 = st.columns(2)
    m1.metric("System Latency", "12ms", "-2ms")
    m2.metric("AI Model", "Gemini 2.0", "Active")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # WORKFLOW VISUALIZER CONTAINER
    workflow_container = st.empty()
    
    # Initialize with "Architect" active if not running, or dynamic if running
    current_node = st.session_state.get("active_node", "architect")
    workflow_container.markdown(render_workflow(current_node), unsafe_allow_html=True)

    # TABS
    st.markdown('<div class="glass-card" style="min-height: 550px;">', unsafe_allow_html=True)
    tabs = st.tabs(["🖥️ TERMINAL", "📝 CODE", "🧪 TESTS", "🛡️ SECURITY"])
    
    with tabs[0]:
        terminal_container = st.empty()
        if not st.session_state.get("running", False):
            terminal_container.markdown('<div class="terminal-window"><div style="color:#666">Waiting for command input...</div></div>', unsafe_allow_html=True)
            
    with tabs[1]: code_container = st.empty()
    with tabs[2]: test_container = st.empty()
    with tabs[3]: sec_container = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# 7. EXECUTION ENGINE
# ---------------------------------------------------
if st.session_state.get("running", False):
    
    initial_code = ""
    if uploaded_file:
        initial_code = uploaded_file.read().decode("utf-8")
        write_file("solution.py", initial_code)
        
    inputs = {
        "objective": objective if objective else "Refactor provided code",
        "code_content": initial_code, "test_content": "", "test_output": "", 
        "security_report": "Pending", "status": "pending", "iterations": 0, "logs": []
    }
    
    # Initialize Log History
    if "logs" not in st.session_state: st.session_state.logs = []
    
    try:
        run_config = {"recursion_limit": 50}
        
        for event in logic_app.stream(inputs, config=run_config):
            for node_name, node_data in event.items():
                if not isinstance(node_data, dict): continue
                
                # 1. Update Workflow Visualizer
                # Map internal node names to visualizer IDs
                visual_node = node_name # default
                if "architect" in node_name: visual_node = "architect"
                elif "developer" in node_name: visual_node = "developer"
                elif "security" in node_name: visual_node = "security"
                elif "tester" in node_name: visual_node = "tester"
                
                workflow_container.markdown(render_workflow(visual_node), unsafe_allow_html=True)

                # 2. Update Logs (Terminal)
                if "logs" in node_data:
                    for log in node_data["logs"]:
                        ts = time.strftime("%H:%M:%S")
                        
                        # Style based on content
                        color = "white"
                        icon = "🔹"
                        if "ARCHITECT" in log: color="#00e5ff"; icon="📐"
                        elif "DEVELOPER" in log: color="#ff00e6"; icon="👨‍💻"
                        elif "TESTER" in log: color="#ffea00"; icon="⚡"
                        elif "SEC" in log: color="#00ff9d"; icon="🛡️"
                        elif "FAIL" in log: color="#ff0055"; icon="❌"
                        elif "SUCCESS" in log: color="#00ff9d"; icon="✅"

                        entry = f"""<div class="log-entry"><span style="color:#444; margin-right:10px;">[{ts}]</span><span style="color:{color};">{icon} {log}</span></div>"""
                        st.session_state.logs.insert(0, entry) # Add to top
                        
                        # Render Terminal
                        log_html = "".join(st.session_state.logs)
                        terminal_container.markdown(f'<div class="terminal-window">{log_html}</div>', unsafe_allow_html=True)
                        time.sleep(0.05) # Tiny typing delay effect

                # 3. Update Artifacts (Code/Tests/Sec)
                if "code_content" in node_data: 
                    code_container.markdown(f"```python\n{node_data['code_content']}\n```")
                
                if "test_content" in node_data: 
                    test_container.markdown(f"```python\n{node_data['test_content']}\n```")
                
                if "security_report" in node_data:
                    report = node_data["security_report"]
                    if "Clear" in report or "No High" in report:
                         sec_container.success("🛡️ SECURITY SCAN PASSED: No Critical Vulnerabilities.")
                         sec_container.markdown(f"```text\n{report}\n```")
                    else:
                        sec_container.error("🚨 VULNERABILITIES DETECTED")
                        sec_container.markdown(f"```text\n{report}\n```")

        # COMPLETE
        workflow_container.markdown(render_workflow("done"), unsafe_allow_html=True)
        st.success("✨ Autonomous Sequence Complete")
        st.balloons() # 🎉 CONFETTI
        st.session_state.running = False

    except Exception as e:
        st.error(f"❌ Execution Failure: {e}")
        st.session_state.running = False