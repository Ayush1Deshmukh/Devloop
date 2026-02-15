import streamlit as st
import os
import sys

# --- 1. CONFIG MUST BE FIRST ---
st.set_page_config(
    page_title="DevLoop Debug",
    page_icon=":wrench:",
    layout="wide"
)

st.title("DevLoop Diagnostic Mode")
st.write("Initializing System...")

# --- 2. PATH SETUP ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    st.success(f"Path set to: {current_dir}")
except Exception as e:
    st.error(f"Path Setup Failed: {e}")
    st.stop()

# --- 3. SECRETS SETUP ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
        st.success("API Key Loaded from Secrets")
    else:
        st.warning("GOOGLE_API_KEY not found in Streamlit Secrets")
except Exception as e:
    st.warning(f"Secrets Error: {e}")

# --- 4. SAFE IMPORT LOGIC ---
st.write("Attempting to import logic...")

try:
    import logic
    import tools
    if hasattr(logic, 'agent_app'):
        logic_app = logic.agent_app
        st.success(f"Logic Module Loaded (Type: {type(logic_app)})")
    else:
        st.error(f"'agent_app' not found in logic.py. Available attributes: {dir(logic)}")
        st.stop()
    write_file = tools.write_file
    st.success("Tools Module Loaded")
except ImportError as e:
    st.error(f"Import Failed: {e}")
    st.info("Check your requirements.txt: streamlit, langgraph, langchain-google-genai")
    st.stop()
except Exception as e:
    st.error(f"Critical System Crash during Import: {e}")
    st.stop()

# --- 5. SIMPLE UI (Test if App Runs) ---
st.divider()
st.subheader("System Ready")
objective = st.text_input("Enter a test objective", "Print hello world")
if st.button("Run Test Agent"):
    with st.spinner("Agent running..."):
        try:
            inputs = {"objective": objective, "code_content": "", "test_content": "", "test_output": "", "status": "pending", "iterations": 0, "logs": []}
            for event in logic_app.stream(inputs):
                st.write(event)
            st.success("Test Completed!")
        except Exception as e:
            st.error(f"Runtime Execution Error: {e}")

# --- 6. DEBUG FOOTER ---
st.markdown("---")
st.caption(f"Python Executable: {sys.executable}")
st.caption(f"Working Directory: {os.getcwd()}")
st.caption(f"Directory Contents: {os.listdir(os.getcwd())}")