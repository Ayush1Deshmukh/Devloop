import streamlit as st
import os
import sys

# --- 1. SECRETS SETUP ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    pass

import streamlit.components.v1 as components
import time
# Ensure logic.py exists in the same folder!
from logic import app as logic_app, write_file 

# --- 2. CONFIG ---
st.set_page_config(
    page_title="DevLoop Prime",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 3. JAVASCRIPT: CURSOR TRACKING ---
# This tracks the mouse and sends coordinates to CSS variables
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

# --- 4. CSS: THE VISUAL ENGINE ---
st.markdown("""
<style>
    /* IMPORTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');

    /* VARS */
    :root {
        --primary: #6366f1;
        --secondary: #ec4899;
        --bg-deep: #050505;
        --glass: rgba(20, 20, 25, 0.7);
        --border: rgba(255, 255, 255, 0.08);
    }

    /* GLOBAL RESET */
    .stApp {
        background-color: var(--bg-deep);
        font-family: 'Inter', sans-serif;
    }

    /* --- BACKGROUND EFFECTS --- */
    
    /* 1. Grid Texture */
    .stApp::before {
        content: ""; position: fixed; inset: 0;
        background-image: radial-gradient(#333 1px, transparent 1px);
        background-size: 40px 40px;
        opacity: 0.15; z-index: 0; pointer-events: none;
    }

    /* 2. Cursor Spotlight (Follows Mouse) */
    .stApp::after {
        content: ""; position: fixed; inset: 0;
        background: radial-gradient(600px circle at var(--x) var(--y), rgba(99, 102, 241, 0.1), transparent 40%);
        z-index: 0; pointer-events: none;
    }

    /* 3. Floating Nebulas (Continuous Animation) */
    .nebula {
        position: fixed; width: 500px; height: 500px;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        filter: blur(120px); opacity: 0.15; border-radius: 50%;
        animation: float 20s infinite alternate; z-index: 0; pointer-events: none;
    }
    .nebula:nth-child(1) { top: -10%; left: -10%; animation-delay: 0s; }
    .nebula:nth-child(2) { bottom: -10%; right: -10%; animation-delay: -10s; background: linear-gradient(135deg, #0ea5e9, #8b5cf6); }

    @keyframes float {
        0% { transform: translate(0, 0) scale(1); }
        100% { transform: translate(50px, 50px) scale(1.1); }
    }

    /* --- GLASS UI COMPONENTS --- */
    
    .glass-card {
        background: var(--glass);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s;
        position: relative; overflow: hidden;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.1);
    }

    /* Navbar Spec */
    .navbar {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 30px; padding: 16px 24px;
    }

    /* --- LOADING GLOW EFFECT --- */
    @keyframes pulse-border {
        0% { border-color: rgba(99, 102, 241, 0.2); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
        70% { border-color: rgba(99, 102, 241, 0.8); box-shadow: 0 0 0 10px rgba(99, 102, 241, 0); }
        100% { border-color: rgba(99, 102, 241, 0.2); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
    }

    .loading-active {
        animation: pulse-border 2s infinite;
    }

    /* --- TERMINAL STYLING --- */
    .terminal {
        background: #09090b; border: 1px solid #27272a; border-radius: 8px;
        font-family: 'JetBrains Mono', monospace; height: 100%;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }
    .terminal-header {
        background: #18181b; padding: 8px 12px; border-bottom: 1px solid #27272a;
        display: flex; gap: 6px;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .logs { 
        padding: 16px; height: 400px; overflow-y: auto; 
        color: #4ade80; font-size: 0.85rem; display: flex; flex-direction: column-reverse;
    }
    .log-line { margin-bottom: 4px; border-left: 2px solid #27272a; padding-left: 8px; }

    /* --- FOOTER --- */
    .footer {
        position: fixed; bottom: 20px; right: 20px;
        background: rgba(0,0,0,0.6); backdrop-filter: blur(10px);
        border: 1px solid var(--border); border-radius: 50px;
        padding: 8px 16px; font-size: 0.8rem; color: #a1a1aa;
        display: flex; gap: 10px; align-items: center; z-index: 100;
        transition: all 0.3s;
    }
    .footer:hover { background: rgba(0,0,0,0.9); border-color: var(--primary); color: white; }
    .footer a { color: inherit; text-decoration: none; display: flex; align-items: center; gap: 6px; }

    /* --- STREAMLIT OVERRIDES --- */
    .stTextArea textarea { background: rgba(0,0,0,0.3) !important; color: white !important; border: 1px solid var(--border) !important; }
    .stTextArea textarea:focus { border-color: var(--primary) !important; box-shadow: 0 0 10px rgba(99,102,241,0.2) !important; }
    div[data-testid="stButton"] button {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        border: none; color: white; font-weight: 600; padding: 10px 24px;
        transition: all 0.3s; width: 100%;
    }
    div[data-testid="stButton"] button:hover {
        transform: scale(1.02); box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
    }
    #MainMenu, footer, header { visibility: hidden; }
</style>

<div class="nebula"></div>
<div class="nebula"></div>
""", unsafe_allow_html=True)

# --- 5. HEADER SECTION ---
st.markdown("""
<div class="glass-card navbar">
    <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:24px;">⚡</span>
        <div>
            <div style="font-weight:700; font-size:1.1rem; letter-spacing:-0.5px;">DEVLOOP PRIME</div>
            <div style="font-size:0.75rem; color:#a1a1aa;">Autonomous Agentic Architecture</div>
        </div>
    </div>
    <div style="font-family:'JetBrains Mono'; font-size:0.8rem; background:rgba(255,255,255,0.05); padding:6px 12px; border-radius:6px;">
        <span style="color:#4ade80;">●</span> SYSTEM ONLINE
    </div>
</div>
""", unsafe_allow_html=True)

# Stats Row
c1, c2, c3, c4 = st.columns(4)
def stat(label, val, sub):
    return f"""<div class="glass-card" style="padding:16px;"><div style="color:#71717a; font-size:0.75rem; font-weight:600;">{label}</div><div style="font-size:1.4rem; font-weight:700; margin:4px 0;">{val}</div><div style="font-size:0.7rem; color:var(--primary);">{sub}</div></div>"""
with c1: st.markdown(stat("NODES", "3 Active", "Architect • Dev • Test"), unsafe_allow_html=True)
with c2: st.markdown(stat("RUNTIME", "Docker", "Isolated Sandbox"), unsafe_allow_html=True)
with c3: st.markdown(stat("MODEL", "Gemini 2.0", "Flash Experimental"), unsafe_allow_html=True)
with c4: st.markdown(stat("LATENCY", "45ms", "Real-time Stream"), unsafe_allow_html=True)

st.write("") # Spacer

# --- 6. MAIN WORKSPACE ---
# Determine if we should apply the "glowing loading" class
load_class = "loading-active" if st.session_state.get("running") else ""

st.markdown(f'<div class="glass-card {load_class}" style="min-height: 600px;">', unsafe_allow_html=True)
col_input, col_output = st.columns([1, 1.8])

with col_input:
    st.markdown("### 💠 Mission Control")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    
    objective = st.text_area("Task Objective", height=150, placeholder="E.g., Write a secure password validation function that requires special characters...", label_visibility="collapsed")
    
    uploaded_file = st.file_uploader("Inject Source Code (Optional)", type=["py"], label_visibility="collapsed")
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    
    if st.button("INITIALIZE SEQUENCE 🚀"):
        st.session_state.running = True
        st.rerun()

with col_output:
    st.markdown("### 📟 Neural Logs")
    tabs = st.tabs(["Execution Log", "Source Code", "Tests", "Security"])
    
    with tabs[0]:
        terminal_container = st.empty()
    
    with tabs[1]:
        code_container = st.empty()
        code_container.code("# Waiting for input...", language="python")

st.markdown('</div>', unsafe_allow_html=True)

# --- 7. FOOTER ---
st.markdown("""
<div class="footer">
    <a href="https://github.com/Ayush1Deshmukh/Devloop" target="_blank">
        <img src="https://img.icons8.com/ios-filled/50/ffffff/github.png" width="16"/>
        <span>github.com/Ayush1Deshmukh/Devloop</span>
    </a>
    <span style="opacity:0.3">|</span>
    <span>Ayush Deshmukh</span>
</div>
""", unsafe_allow_html=True)


# --- 8. EXECUTION LOGIC (BACKEND CONNECTION) ---
if st.session_state.get("running", False):
    
    # 1. Setup Input
    initial_code = ""
    if uploaded_file:
        initial_code = uploaded_file.read().decode("utf-8")
        write_file("solution.py", initial_code)
    
    if not objective and not initial_code:
        st.warning("⚠️ Please provide an objective or file.")
        st.session_state.running = False
        st.stop()

    inputs = {
        "objective": objective if objective else "Refactor provided code",
        "code_content": initial_code,
        "test_content": "", "test_output": "", "status": "pending", "iterations": 0, "logs": []
    }

    # 2. Run Stream
    logs_history = []
    
    try:
        # We assume logic.py has been updated to yield 'logs' in the state
        for event in logic_app.stream(inputs):
            for node_name, node_data in event.items():
                
                # A. Update Terminal
                if "logs" in node_data:
                    for log in node_data["logs"]:
                        ts = time.strftime("%H:%M:%S")
                        # Add colored icon based on role
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
                        logs_history.insert(0, entry) # Prepend for reverse order
                        
                        # Render Terminal
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
                        time.sleep(0.05) # Typewriter effect feel

                # B. Update Code Tabs
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
