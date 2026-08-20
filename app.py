import html
import os
import re
import sys
import time

import streamlit as st

# ---------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------
st.set_page_config(
    page_title="DevLoop Prime | Autonomous Architect",
    page_icon="⚡",
    layout="wide",
    # Expanded, not collapsed: the key/quota controls live here now, and a
    # visitor whose run is blocked on a missing key needs to see why without
    # hunting for a hamburger.
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------
# 2. SAFE IMPORT LOGIC
# ---------------------------------------------------
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        from logic import (BACKUP_MODEL, MAX_ITERATIONS, PRIMARY_MODEL,
                           create_agent, get_owner_api_key, verify_api_key)
        from tools import sandbox_backend, write_file
    except ImportError:
        from app.logic import (BACKUP_MODEL, MAX_ITERATIONS, PRIMARY_MODEL,
                               create_agent, get_owner_api_key, verify_api_key)
        from app.tools import sandbox_backend, write_file
except Exception as e:
    st.error(f"⚠️ Critical System Error: {e}")
    st.stop()

# ---------------------------------------------------
# 2b. API KEY POLICY
# ---------------------------------------------------
# The deployer's key powers a few free runs per visitor; after that a visitor
# can paste their own key to keep going. This keeps a public demo permanently
# usable on free tiers without a stranger draining the owner's daily quota.


def _setting(name, default):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


FREE_RUNS_PER_SESSION = int(_setting("FREE_RUNS_PER_SESSION", "3"))
OWNER_KEY = get_owner_api_key()

PRESETS = {
    "Custom objective…": "",
    "🔐 Secure login (SQLi-safe)": "Write a secure login function with SQL injection protection",
    "🌐 User registration API": "Create a REST API endpoint for user registration",
    "🛰️ Multi-threaded port scanner": "Build a multi-threaded port scanner",
    "📊 CSV stats parser": "Parse a CSV file and return mean, median and mode for each numeric column",
}

# Defaults for every piece of session state, declared once so widget keys and
# the result renderer can't disagree about what exists yet.
_DEFAULTS = {
    "running": False,
    "just_finished": None,
    "logs": [],
    "runs_used": 0,
    "active_node": None,
    "objective": "",
    "code_content": "",
    "test_content": "",
    "security_report": "",
    "security_ok": None,
    "iterations": 0,
    "final_status": None,
    "key_check": None,
}
for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


def resolve_api_key():
    """Returns (key, source) where source is 'visitor', 'demo' or None."""
    visitor_key = st.session_state.get("visitor_key", "").strip()
    if visitor_key:
        return visitor_key, "visitor"
    if OWNER_KEY and st.session_state.runs_used < FREE_RUNS_PER_SESSION:
        return OWNER_KEY, "demo"
    return None, None


# `docker inspect` costs ~100ms and Streamlit reruns the whole script on every
# keystroke, so cache the probe rather than shelling out constantly.
@st.cache_data(ttl=30, show_spinner=False)
def _cached_backend():
    return sandbox_backend()


# ---------------------------------------------------
# 3. DESIGN SYSTEM
# ---------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg: #06080f;
    --surface: #0d1120;
    --surface-2: #141a2e;
    --line: rgba(255,255,255,0.07);
    --line-strong: rgba(255,255,255,0.14);
    --cyan: #22d3ee;
    --violet: #a78bfa;
    --green: #34d399;
    --amber: #fbbf24;
    --red: #fb7185;
    --txt: #e8ecf6;
    --txt-dim: #8b95ad;
    --mono: 'JetBrains Mono', ui-monospace, monospace;
}

/* ---------- GLOBAL ---------- */
.stApp {
    background:
        radial-gradient(900px 500px at 15% -10%, rgba(34,211,238,0.07), transparent 60%),
        radial-gradient(700px 400px at 88% 0%, rgba(167,139,250,0.07), transparent 60%),
        var(--bg);
    font-family: 'Inter', sans-serif;
    color: var(--txt);
}
.block-container { padding-top: 2.2rem; max-width: 1500px; }
#MainMenu, footer { visibility: hidden; }

h1,h2,h3,h4 { font-family: 'Inter', sans-serif; letter-spacing: -0.02em; }

/* ---------- HEADER ---------- */
.hero {
    display: flex; align-items: center; justify-content: space-between;
    gap: 24px; flex-wrap: wrap;
    padding: 22px 28px; margin-bottom: 22px;
    border: 1px solid var(--line); border-radius: 18px;
    background: linear-gradient(135deg, rgba(34,211,238,0.08), rgba(167,139,250,0.06) 55%, transparent);
}
.hero-title {
    font-size: 2.1rem; font-weight: 800; margin: 0; line-height: 1.1;
    background: linear-gradient(92deg, #ffffff 10%, var(--cyan) 55%, var(--violet));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { color: var(--txt-dim); font-size: .9rem; margin-top: 6px; }
.pill-row { display: flex; gap: 10px; flex-wrap: wrap; }
.pill {
    display: inline-flex; align-items: center; gap: 7px;
    font-family: var(--mono); font-size: .72rem; letter-spacing: .04em;
    padding: 7px 13px; border-radius: 999px;
    border: 1px solid var(--line-strong); background: rgba(255,255,255,0.03);
    color: var(--txt-dim); white-space: nowrap;
}
.pill b { color: var(--txt); font-weight: 500; }
.dot-live {
    width: 7px; height: 7px; border-radius: 50%; background: var(--green);
    box-shadow: 0 0 8px var(--green); animation: breathe 2s ease-in-out infinite;
}
.dot-warn { width: 7px; height: 7px; border-radius: 50%; background: var(--amber); box-shadow: 0 0 8px var(--amber); }
@keyframes breathe { 0%,100% { opacity: 1 } 50% { opacity: .35 } }

/* ---------- CARDS ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0));
    border: 1px solid var(--line) !important;
    border-radius: 16px; padding: 20px 22px;
}
.card-title {
    font-family: var(--mono); font-size: .72rem; letter-spacing: .12em;
    text-transform: uppercase; color: var(--txt-dim);
    padding-bottom: 10px; margin-bottom: 16px; border-bottom: 1px solid var(--line);
}

/* ---------- STEPPER ---------- */
.stepper { position: relative; padding: 26px 8px 34px; margin-bottom: 6px; }
.track {
    position: absolute; top: 47px; left: 46px; right: 46px; height: 2px;
    background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;
}
.track-fill {
    height: 100%; border-radius: 2px;
    background: linear-gradient(90deg, var(--cyan), var(--violet));
    box-shadow: 0 0 12px rgba(34,211,238,.6);
    transition: width .45s cubic-bezier(.4,0,.2,1);
}
.steps { position: relative; display: flex; justify-content: space-between; z-index: 1; }
.step { display: flex; flex-direction: column; align-items: center; gap: 10px; width: 92px; }
.dot {
    width: 44px; height: 44px; border-radius: 50%; font-size: 19px;
    display: flex; align-items: center; justify-content: center;
    background: var(--surface); border: 2px solid rgba(255,255,255,0.12);
    transition: all .3s ease;
}
.cap {
    font-family: var(--mono); font-size: .63rem; letter-spacing: .1em;
    text-transform: uppercase; color: #5c6580; font-weight: 700;
}
.step.active .dot {
    border-color: var(--cyan); background: rgba(34,211,238,0.12);
    box-shadow: 0 0 0 5px rgba(34,211,238,0.10), 0 0 20px rgba(34,211,238,0.45);
    animation: ping 1.8s ease-out infinite;
}
.step.active .cap { color: var(--cyan); }
.step.done .dot { border-color: var(--green); background: rgba(52,211,153,0.12); }
.step.done .cap { color: var(--green); }
@keyframes ping {
    0%   { box-shadow: 0 0 0 0 rgba(34,211,238,.45), 0 0 20px rgba(34,211,238,.4); }
    70%  { box-shadow: 0 0 0 14px rgba(34,211,238,0), 0 0 20px rgba(34,211,238,.4); }
    100% { box-shadow: 0 0 0 0 rgba(34,211,238,0), 0 0 20px rgba(34,211,238,.4); }
}

/* ---------- TERMINAL ---------- */
.term {
    background: #04060d; border: 1px solid var(--line); border-radius: 12px;
    font-family: var(--mono); font-size: .8rem; line-height: 1.55;
    height: 430px; overflow-y: auto;
}
.term-bar {
    position: sticky; top: 0; display: flex; align-items: center; gap: 8px;
    padding: 10px 14px; background: #080b15; border-bottom: 1px solid var(--line);
    border-radius: 12px 12px 0 0; color: #4d5codd; font-size: .7rem;
}
.tl { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.term-path { color: #55607a; margin-left: 6px; letter-spacing: .04em; }
.term-body { padding: 12px 14px; }
.row {
    display: flex; gap: 12px; padding: 5px 0;
    border-bottom: 1px solid rgba(255,255,255,0.035);
    animation: slide .25s ease-out;
}
.ts { color: #3f4860; flex-shrink: 0; }
@keyframes slide { from { opacity:0; transform: translateY(-3px) } to { opacity:1; transform:none } }
.term::-webkit-scrollbar { width: 8px; }
.term::-webkit-scrollbar-thumb { background: #1e2540; border-radius: 8px; }

.empty {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 8px; height: 240px; color: #4b556e;
    border: 1px dashed var(--line-strong); border-radius: 12px; text-align: center;
}
.empty .big { font-size: 30px; opacity: .65; }
.empty .sm { font-family: var(--mono); font-size: .74rem; letter-spacing: .05em; }

/* ---------- INPUTS ---------- */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    background-color: #080c17 !important; color: var(--txt) !important;
    border: 1px solid var(--line-strong) !important; border-radius: 10px !important;
}
.stTextArea textarea { font-family: var(--mono) !important; font-size: .85rem !important; }
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--cyan) !important; box-shadow: 0 0 0 3px rgba(34,211,238,0.14) !important;
}

/* ---------- BUTTONS ---------- */
div[data-testid="stButton"] button {
    width: 100%; border-radius: 10px; border: 1px solid var(--line-strong);
    background: rgba(255,255,255,0.04); color: var(--txt);
    font-weight: 600; letter-spacing: .02em; transition: all .2s ease;
}
div[data-testid="stButton"] button:hover:not(:disabled) {
    border-color: var(--line-strong); background: rgba(255,255,255,0.08); color: #fff;
}
div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(95deg, var(--cyan), #6366f1);
    border: none; color: #04060d; font-weight: 800;
    text-transform: uppercase; letter-spacing: .09em; padding: .78rem;
}
div[data-testid="stButton"] button[kind="primary"]:hover:not(:disabled) {
    box-shadow: 0 8px 26px rgba(34,211,238,0.32); transform: translateY(-1px); color: #04060d;
}
div[data-testid="stButton"] button:disabled { opacity: .4; }

/* ---------- TABS ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
    height: 40px; border-radius: 8px 8px 0 0; padding: 0 16px;
    font-family: var(--mono); font-size: .74rem; letter-spacing: .06em; color: var(--txt-dim);
}
.stTabs [aria-selected="true"] { background: rgba(34,211,238,0.09); color: var(--cyan) !important; }

/* ---------- MISC ---------- */
div[data-testid="stMetricValue"] { font-family: var(--mono); font-size: 1.25rem; }
div[data-testid="stMetricLabel"] { color: var(--txt-dim); }
section[data-testid="stSidebar"] { background: #080b14; border-right: 1px solid var(--line); }
code { font-family: var(--mono) !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 4. UI COMPONENTS
# ---------------------------------------------------
STEPS = [
    ("architect", "📐", "Plan"),
    ("developer", "👨‍💻", "Code"),
    ("security", "🛡️", "Secure"),
    ("tester", "⚡", "Test"),
]


def render_stepper(active_node):
    """Draws the pipeline with a progress line that fills as stages complete."""
    ids = [s[0] for s in STEPS]
    idx = ids.index(active_node) if active_node in ids else -1
    done_all = active_node == "done"

    # The track spans centre-to-centre of the first and last dot, so the fill
    # fraction is (completed gaps / total gaps), not (completed / total).
    pct = 100 if done_all else (max(idx, 0) / (len(STEPS) - 1) * 100 if idx >= 0 else 0)

    # NOTE: this HTML must stay free of leading indentation. Streamlit runs it
    # through Markdown first, and any 4-space-indented line becomes a literal
    # code block instead of markup.
    html = ['<div class="stepper">']
    html.append(f'<div class="track"><div class="track-fill" style="width:{pct:.0f}%"></div></div>')
    html.append('<div class="steps">')
    for i, (sid, icon, label) in enumerate(STEPS):
        if done_all or idx > i:
            cls = "done"
        elif idx == i:
            cls = "active"
        else:
            cls = ""
        mark = "✓" if (done_all or idx > i) else icon
        html.append(f'<div class="step {cls}"><div class="dot">{mark}</div><div class="cap">{label}</div></div>')
    html.append("</div></div>")
    return "".join(html)


LOG_STYLES = [
    ("ARCHITECT", "#22d3ee"), ("DEVELOPER", "#a78bfa"), ("TESTER", "#fbbf24"),
    ("SEC-OPS", "#34d399"), ("SUCCESS", "#34d399"), ("FAIL", "#fb7185"),
]


def log_row(message):
    color = "#c3cbdd"
    for token, hexcode in LOG_STYLES:
        if token in message:
            color = hexcode
            break
    # Log text can contain generated code and raw API error bodies, so escape it
    # before it goes into the terminal's innerHTML. Markdown emphasis is then
    # re-applied deliberately, since this pane is HTML rather than Markdown and
    # otherwise showed literal `**asterisks**`.
    safe = html.escape(message)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    ts = time.strftime("%H:%M:%S")
    return (f'<div class="row"><span class="ts">{ts}</span>'
            f'<span style="color:{color}">{safe}</span></div>')


def terminal_html(rows):
    body = "".join(rows) if rows else (
        '<div style="color:#4b556e">Idle. Define an objective and start the sequence…</div>'
    )
    return (
        '<div class="term">'
        '<div class="term-bar">'
        '<span class="tl" style="background:#fb7185"></span>'
        '<span class="tl" style="background:#fbbf24"></span>'
        '<span class="tl" style="background:#34d399"></span>'
        '<span class="term-path">root@devloop ~ ./execute_sequence.sh</span>'
        '</div>'
        f'<div class="term-body">{body}</div></div>'
    )


def empty_state(icon, text):
    return f'<div class="empty"><div class="big">{icon}</div><div class="sm">{text}</div></div>'


def render_security(slot, report, ok):
    """Paints the security tab. Shared by the persisted render and the live run
    so the two can't drift apart."""
    with slot.container():
        if ok:
            st.success("🛡️ No blocking vulnerabilities")
        else:
            st.error("🚨 High-severity vulnerabilities detected")
        st.code(report, language="text")


def apply_node_update(node_data, slots):
    """Mirrors one LangGraph node's output into session state and the live UI.

    Extracted from the streaming loop, which had grown to a cyclomatic
    complexity of 19 and inlined a second copy of the security renderer.
    """
    stepper, term, code, test, sec, iters_metric = slots

    for message in node_data.get("logs", []):
        st.session_state.logs.insert(0, log_row(message))
        term.markdown(terminal_html(st.session_state.logs), unsafe_allow_html=True)
        time.sleep(0.05)  # Tiny typing-effect delay.

    if "code_content" in node_data:
        st.session_state.code_content = node_data["code_content"]
        code.code(node_data["code_content"], language="python")

    if "test_content" in node_data:
        st.session_state.test_content = node_data["test_content"]
        test.code(node_data["test_content"], language="python")

    if "iterations" in node_data:
        st.session_state.iterations = node_data["iterations"]
        iters_metric.metric("Last cycles", node_data["iterations"])

    if "security_report" in node_data:
        st.session_state.security_report = node_data["security_report"]
        st.session_state.security_ok = node_data.get("security_ok", True)
        render_security(sec, node_data["security_report"], st.session_state.security_ok)


# ---------------------------------------------------
# 5. SIDEBAR — credentials, config, telemetry
# ---------------------------------------------------
active_key, key_source = resolve_api_key()
backend = _cached_backend()

with st.sidebar:
    st.markdown('<div class="card-title">Access</div>', unsafe_allow_html=True)

    runs_left = max(0, FREE_RUNS_PER_SESSION - st.session_state.runs_used)
    if key_source == "demo":
        st.success(f"🎁 Demo mode — **{runs_left}/{FREE_RUNS_PER_SESSION}** free runs left")
    elif key_source == "visitor":
        st.success("🔑 Using your own Gemini key — unlimited runs")
    elif OWNER_KEY:
        st.warning("🎁 Free demo runs used up. Add your own key below.")
    else:
        st.error("🔑 No key configured. Add your own Gemini key below.")

    st.text_input(
        "Gemini API key",
        type="password",
        key="visitor_key",
        placeholder="AIza…",
        help="Free at aistudio.google.com/app/apikey. Held in your browser session "
             "only — never logged or stored.",
    )

    # A live diagnostic beats a generic failure message: a suspended, invalid or
    # wrong-project key all produce the same unhelpful error mid-run otherwise.
    if st.button("🩺 Test this key", use_container_width=True):
        with st.spinner("Asking Google…"):
            st.session_state.key_check = verify_api_key(active_key or "")

    if st.session_state.key_check:
        ok, msg, models = st.session_state.key_check
        (st.success if ok else st.error)(msg)
        if models:
            with st.expander(f"{len(models)} available models"):
                st.code("\n".join(models), language="text")

    st.markdown('<div class="card-title" style="margin-top:22px">Runtime</div>', unsafe_allow_html=True)
    st.caption(f"**Primary model** · `{PRIMARY_MODEL}`")
    st.caption(f"**Fallback model** · `{BACKUP_MODEL}`")
    st.caption(f"**Max self-heal cycles** · `{MAX_ITERATIONS}`")

    if backend == "docker":
        st.caption("**Sandbox** · 🐳 Docker container (full isolation)")
    else:
        st.caption("**Sandbox** · 🧱 rlimit + temp dir (no container isolation)")

    st.markdown('<div class="card-title" style="margin-top:22px">Telemetry</div>', unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    telemetry_runs = t1.empty()
    telemetry_iters = t2.empty()
    telemetry_runs.metric("Runs", st.session_state.runs_used)
    telemetry_iters.metric("Last cycles", st.session_state.iterations)

# ---------------------------------------------------
# 6. HEADER
# ---------------------------------------------------
sandbox_pill = (
    '<span class="pill"><span class="dot-live"></span>SANDBOX <b>Docker</b></span>'
    if backend == "docker" else
    '<span class="pill"><span class="dot-warn"></span>SANDBOX <b>rlimit</b></span>'
)
st.markdown(
    '<div class="hero">'
    '<div><h1 class="hero-title">DevLoop Prime</h1>'
    '<div class="hero-sub">Autonomous DevSecOps engine — writes tests, writes code, '
    'scans it, runs it, and fixes itself until it passes.</div></div>'
    f'<div class="pill-row">'
    f'<span class="pill"><span class="dot-live"></span>ENGINE <b>Online</b></span>'
    f'<span class="pill">MODEL <b>{PRIMARY_MODEL}</b></span>'
    f'{sandbox_pill}</div></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# 7. WORKSPACE
# ---------------------------------------------------
col_left, col_right = st.columns([1, 1.75], gap="large")

with col_left, st.container(border=True):
    st.markdown('<div class="card-title">Mission parameters</div>', unsafe_allow_html=True)

    def _apply_preset():
        chosen = PRESETS.get(st.session_state.preset, "")
        if chosen:
            st.session_state.objective = chosen

    st.selectbox("Template", list(PRESETS), key="preset", on_change=_apply_preset)
    st.text_area(
        "Objective",
        key="objective",
        height=130,
        placeholder="Describe the module to build…",
    )
    uploaded_file = st.file_uploader("Seed with existing code (optional)", type=["py"])

    st.write("")
    launch = st.button(
        "🚀 Initialize sequence",
        type="primary",
        disabled=active_key is None or st.session_state.running,
        use_container_width=True,
    )
    if active_key is None:
        st.caption("⚠️ Add a Gemini API key in the sidebar to enable launch.")

    if launch:
        if not st.session_state.objective.strip() and not uploaded_file:
            st.warning("Protocol halted — no objective given.")
        else:
            st.session_state.update(
                running=True, logs=[], active_node="architect", just_finished=None,
                code_content="", test_content="", security_report="",
                security_ok=None, iterations=0, final_status=None,
            )
            st.rerun()

with col_right:
    stepper_slot = st.empty()
    stepper_slot.markdown(
        render_stepper(st.session_state.active_node or ("done" if st.session_state.final_status == "success" else None)),
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        tab_term, tab_code, tab_test, tab_sec = st.tabs(
            ["🖥️ TERMINAL", "📝 SOLUTION", "🧪 TESTS", "🛡️ SECURITY"]
        )

        with tab_term:
            term_slot = st.empty()
            term_slot.markdown(terminal_html(st.session_state.logs), unsafe_allow_html=True)

        # Each artifact tab renders from session_state first, so results survive
        # the reruns Streamlit fires on any later widget interaction. Live
        # placeholders overwrite these during a run.
        with tab_code:
            code_slot = st.empty()
            if st.session_state.code_content:
                code_slot.code(st.session_state.code_content, language="python")
                st.download_button(
                    "⬇️ solution.py", st.session_state.code_content,
                    file_name="solution.py", mime="text/x-python",
                )
            else:
                code_slot.markdown(empty_state("📝", "No implementation yet"), unsafe_allow_html=True)

        with tab_test:
            test_slot = st.empty()
            if st.session_state.test_content:
                test_slot.code(st.session_state.test_content, language="python")
                st.download_button(
                    "⬇️ test_solution.py", st.session_state.test_content,
                    file_name="test_solution.py", mime="text/x-python",
                )
            else:
                test_slot.markdown(empty_state("🧪", "No tests yet"), unsafe_allow_html=True)

        with tab_sec:
            sec_slot = st.empty()
            if st.session_state.security_report:
                render_security(
                    sec_slot,
                    st.session_state.security_report,
                    st.session_state.security_ok,
                )
            else:
                sec_slot.markdown(empty_state("🛡️", "No scan yet"), unsafe_allow_html=True)

# Post-run banner. Rendered after a rerun so the finished results are already
# painted from session_state underneath it.
if st.session_state.just_finished:
    kind, text = st.session_state.just_finished
    {"success": st.success, "warning": st.warning, "error": st.error}[kind](text)
    if kind == "success":
        st.balloons()
    st.session_state.just_finished = None

# ---------------------------------------------------
# 8. EXECUTION ENGINE
# ---------------------------------------------------
if st.session_state.running:
    if active_key is None:
        st.session_state.running = False
        st.error("🔑 No API key available for this session.")
        st.stop()

    # Bind the agent to this session's key only — never a process-wide global.
    agent = create_agent(active_key)

    # Count the run against the demo quota (a visitor's own key is unlimited).
    if key_source == "demo":
        st.session_state.runs_used += 1
        telemetry_runs.metric("Runs", st.session_state.runs_used)

    initial_code = ""
    if uploaded_file:
        initial_code = uploaded_file.read().decode("utf-8")
        write_file("solution.py", initial_code)

    inputs = {
        "objective": st.session_state.objective.strip() or "Refactor the provided code",
        "code_content": initial_code, "test_content": "", "test_output": "",
        "security_report": "", "status": "pending", "iterations": 0, "logs": [],
    }

    try:
        final_status = "pending"

        slots = (stepper_slot, term_slot, code_slot, test_slot, sec_slot, telemetry_iters)

        for event in agent.stream(inputs, config={"recursion_limit": 50}):
            for node_name, node_data in event.items():
                if not isinstance(node_data, dict):
                    continue
                if "status" in node_data:
                    final_status = node_data["status"]
                stepper_slot.markdown(render_stepper(node_name), unsafe_allow_html=True)
                apply_node_update(node_data, slots)

        st.session_state.running = False
        st.session_state.final_status = final_status
        st.session_state.active_node = "done" if final_status == "success" else None

        # Report what actually happened rather than always celebrating.
        if final_status == "success":
            st.session_state.just_finished = ("success", "✨ Sequence complete — tests green, scan clear.")
        elif final_status == "error":
            st.session_state.just_finished = (
                "error",
                "🛑 Sequence aborted — the AI engine or the test runner was unreachable. "
                "See the terminal log for details.",
            )
        else:
            st.session_state.just_finished = (
                "warning",
                f"⚠️ No passing build after {MAX_ITERATIONS} self-heal cycles. "
                "Review the solution and test tabs.",
            )

        # Rerun so every tab re-renders from session_state — that's what keeps the
        # results (and their download buttons) alive through later interactions.
        st.rerun()

    except Exception as e:
        st.session_state.running = False
        st.error(f"❌ Execution failure: {e}")
