import streamlit as st
import os
import sys

# --- CRITICAL FIX: Load API Key from Secrets to Environment ---
# We must do this BEFORE importing logic.py, or the app will crash.
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    # This handles the case where you are running locally without secrets.toml
    pass

# --- NOW imports can happen safely ---
import streamlit.components.v1 as components
import time
import base64
from logic import app, write_file

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DevLoop Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. JAVASCRIPT CURSOR TRACKING ---
components.html(
    """
    <script>
    document.addEventListener('mousemove', function(e) {
        let x = e.clientX;
        let y = e.clientY;
        window.parent.document.documentElement.style.setProperty('--cursor-x', x + 'px');
        window.parent.document.documentElement.style.setProperty('--cursor-y', y + 'px');
    });
    </script>
    """,
    height=0, width=0
)

# --- 3. ADVANCED CSS ---
st.markdown("""
<style>
    /* FONTS & VARS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');
    :root { --cursor-x: 50vw; --cursor-y: 50vh; --primary: #6366f1; --secondary: #a855f7; }
    
    /* BASE LAYERS & ANIMATED BACKGROUND */
    .stApp {
        background-color: #050505;
        font-family: 'Inter', sans-serif;
        overflow-x: hidden;
    }
    
    /* Layer 1: Circuit Pattern */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M54.627 0l.83.828-1.415 1.415L51.8 0h2.827zM5.373 0l-.83.828L5.96 2.243 8.2 0H5.374zM48.97 0l3.657 3.657-1.414 1.414L46.143 0h2.828zM11.03 0L7.372 3.657 8.787 5.07 13.857 0h-2.828zM0 5.373l.828-.83 1.415 1.415L0 8.2V5.373zm0 48.254l.828.83-1.415 1.415L0 51.8v2.827zm0-11.03l3.657-3.657 1.414 1.414L0 46.143v-2.828zm0-2.828l5.07-5.07 1.415 1.415L0 43.97v-2.828zm60 0l-5.07-5.07-1.415 1.415L60 43.97v-2.828zm0-11.03l-3.657-3.657-1.414 1.414L60 46.143v-2.828zm0 13.858l-.828.83 1.415 1.415L60 51.8v-2.827zm0-48.254l-.828-.83 1.415 1.415L60 8.2V5.373zM51.8 60l2.243-2.243 1.415 1.415L54.627 60h-2.827zM8.2 60L5.96 57.757 4.543 59.172 5.373 60H8.2zM46.143 60l5.07-5.07 1.415 1.415L48.97 60h-2.828zM13.857 60l-5.07-5.07-1.415 1.415L11.03 60h2.827z' fill='%232a2a2a' fill-opacity='0.4' fill-rule='evenodd'/%3E%3C/svg%3E");
        opacity: 0.5;
        z-index: 0;
    }

    /* Layer 2: Moving Energy Fog */
    @keyframes drift { from { background-position: 0 0; } to { background-position: 100% 100%; } }
    .stApp::after {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 60%);
        background-size: 50% 50%;
        animation: drift 60s linear infinite;
        opacity: 0.6;
        z-index: 1;
        pointer-events: none;
    }

    /* Layer 3: Cursor Reactive Glow */
    .cursor-glow {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(600px circle at var(--cursor-x) var(--cursor-y), rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.1), transparent 40%);
        z-index: 2;
        pointer-events: none;
    }

    /* --- LOADING ANIMATION (DATA STREAM) --- */
    @keyframes datastream {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .loading-active {
        position: relative;
        border-radius: 12px;
    }
    .loading-active::before {
        content: "";
        position: absolute;
        inset: -2px;
        z-index: -1;
        background: linear-gradient(90deg, var(--primary), var(--secondary), var(--primary));
        background-size: 200% 200%;
        animation: datastream 3s linear infinite;
        border-radius: 14px;
        filter: blur(8px);
        opacity: 0.7;
    }

    /* --- UI COMPONENTS (Glassmorphism) --- */
    .glass {
        background: rgba(24, 24, 27, 0.7);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        z-index: 10; position: relative;
    }
    .navbar { padding: 1rem 1.5rem; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
    .brand { font-weight: 700; font-size: 1.2rem; display: flex; align-items: center; gap: 0.8rem; color: #fff; letter-spacing: -0.5px; }
    .stat-card { padding: 1.25rem; border-radius: 12px; transition: all 0.3s; }
    .stat-card:hover { transform: translateY(-3px); border-color: var(--primary); box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.3); }
    .stat-value { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.5rem; margin-top: 4px; background: linear-gradient(to right, #fff, #a1a1aa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* TERMINAL STYLES */
    .terminal { background: #09090b; border-radius: 10px; border: 1px solid #27272a; font-family: 'JetBrains Mono', monospace; overflow: hidden; box-shadow: 0 20px 40px -20px rgba(0,0,0,0.5); }
    .terminal-bar { background: #18181b; padding: 8px 12px; display: flex; gap: 8px; border-bottom: 1px solid #27272a; }
    .logs-area { padding: 16px; height: 450px; overflow-y: auto; color: #22c55e; font-size: 0.85rem; }
    .log-entry { margin-bottom: 6px; display: flex; gap: 12px; }
    .timestamp { color: #52525b; user-select: none; }

    /* FOOTER */
    .footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        padding: 1rem; text-align: center;
        background: rgba(9, 9, 11, 0.8); backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        color: #71717a; font-size: 0.85rem; z-index: 50;
    }
    .footer a { color: #a1a1aa; text-decoration: none; transition: color 0.2s; }
    .footer a:hover { color: var(--primary); }

    /* HIDE DEFAULT STREAMLIT */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 4rem; }
    .stTextArea textarea { background: rgba(24, 24, 27, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    div[data-testid="stButton"] > button:first-child { background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; font-weight: 600; padding: 0.75rem 1.5rem; transition: all 0.3s; }
    div[data-testid="stButton"] > button:first-child:hover { box-shadow: 0 0 25px rgba(99, 102, 241, 0.5); transform: scale(1.02); }
</style>
<div class="cursor-glow"></div>
""", unsafe_allow_html=True)

# --- 4. UI BODY ---

# Navbar
st.markdown("""
<div class="navbar glass">
    <div class="brand">
        <span style="font-size: 1.5rem;">⚡</span>
        <span>DevLoop Prime</span>
        <span style="background:rgba(99,102,241,0.2); color:#818cf8; font-size:0.7rem; padding:2px 8px; border-radius:12px; border:1px solid rgba(99,102,241,0.4);">V5.0</span>
    </div>
    <div style="display: flex; gap: 1.5rem; align-items: center; font-size: 0.9rem; color: #a1a1aa;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width:8px; height:8px; background:#22c55e; border-radius:50%; box-shadow:0 0 10px #22c55e;"></div>
            <span>Neural Engine Active</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Metrics
m1, m2, m3, m4 = st.columns(4)
def stat_box(label, value, icon):
    return f"""<div class="stat-card glass"><div style="color:#71717a; font-size:0.8rem; text-transform:uppercase; display:flex; justify-content:space-between;"><span>{label}</span><span>{icon}</span></div><div class="stat-value">{value}</div></div>"""
with m1: st.markdown(stat_box("Architecture", "Agentic State Graph", "🕸️"), unsafe_allow_html=True)
with m2: st.markdown(stat_box("Runtime", "Docker Isolated", "🧊"), unsafe_allow_html=True)
with m3: st.markdown(stat_box("Model", "Gemini 2.0 Flash", "🧠"), unsafe_allow_html=True)
with m4: st.markdown(stat_box("Security", "Bandit SecOps", "🛡️"), unsafe_allow_html=True)
st.write("")

# --- MAIN WORKSPACE (With Conditional Loading Effect) ---
is_running = st.session_state.get("running", False)
loading_class = "loading-active" if is_running else ""

st.markdown(f'<div class="{loading_class}" style="padding: 2px; transition: all 0.3s;">', unsafe_allow_html=True)
st.markdown('<div class="glass" style="padding: 24px; border-radius: 12px;">', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.6])

with col_left:
    st.markdown("### Mission Directive")
    objective = st.text_area("objective", placeholder="Enter engineering task or security audit request...", height=120, label_visibility="collapsed")
    uploaded_file = st.file_uploader("Upload Source Code", type=["py"], label_visibility="collapsed")
    st.write("")
    if st.button("Initialize Sequence →"):
        st.session_state.running = True
        st.rerun()

with col_right:
    st.markdown("### Engineering Console")
    tab_code, tab_test, tab_sec, tab_term = st.tabs(["📄 Code", "🧪 Tests", "🛡️ Audit", "📟 Output"])

st.markdown('</div></div>', unsafe_allow_html=True)

# --- EXECUTION LOGIC ---
if is_running:
    initial_code = ""
    if uploaded_file:
        initial_code = uploaded_file.read().decode("utf-8")
        write_file("solution.py", initial_code)
        if not objective: objective = "Refactor this code to fix security issues."

    if not objective and not uploaded_file:
        st.warning("Input required.")
        st.session_state.running = False
        st.stop()

    inputs = {"objective": objective, "code_content": initial_code, "test_content": "", "test_output": "", "security_report": "", "status": "pending", "iterations": 0, "logs": []}
    
    with col_left:
        st.write("")
        terminal_placeholder = st.empty()
    logs_history = []

    try:
        for event in app.stream(inputs):
            for node_name, node_data in event.items():
                if "logs" in node_data:
                    for log in node_data["logs"]:
                        ts = time.strftime("%H:%M:%S")
                        logs_history.append(f"<div class='log-entry'><span class='timestamp'>{ts}</span> <span>{log}</span></div>")
                        log_html = "".join(logs_history)
                        terminal_placeholder.markdown(f"""<div class="terminal"><div class="terminal-bar"><div style="width:10px;height:10px;background:#ff5f56;border-radius:50%"></div><div style="width:10px;height:10px;background:#ffbd2e;border-radius:50%"></div><div style="width:10px;height:10px;background:#27c93f;border-radius:50%"></div></div><div class="logs-area">{log_html}<div style="margin-top:4px;color:#fff;animation:blink 1s infinite">_</div></div></div><style>@keyframes blink{{50%{{opacity:0}}}}</style>""", unsafe_allow_html=True)
                        time.sleep(0.05)
                if "code_content" in node_data:
                    with tab_code: st.code(node_data["code_content"], language="python", line_numbers=True)
                if "test_content" in node_data:
                    with tab_test: st.code(node_data["test_content"], language="python", line_numbers=True)
                if "security_report" in node_data:
                    with tab_sec:
                        rep = node_data["security_report"]
                        if "VULNERABILITIES" in rep: st.error(rep, icon="🚨")
                        else: st.success(rep, icon="✅")
                if "test_output" in node_data:
                    with tab_term:
                        if node_data["status"] == "success": st.success(f"SUCCESS:\n{node_data['test_output']}")
                        else: st.error(f"FAILURE:\n{node_data['test_output']}")
        st.session_state.running = False
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
        st.session_state.running = False
        st.rerun()

# --- 5. FOOTER ---
st.markdown("""
<div class="footer">
    Engineered by <b>Ayush Deshmukh</b> | 
    <a href="https://github.com/Ayush1Deshmukh/Devloop" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" width="16" style="vertical-align:middle; margin-right:4px; opacity:0.7;">
        GitHub Repository
    </a>
</div>
""", unsafe_allow_html=True)
