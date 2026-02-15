import subprocess
import os


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def run_test(filename="solution.py", test_file="test_solution.py"):
    # Check if we are running in a restricted cloud environment (like Streamlit)
    is_cloud = os.getenv("STREAMLIT_CLOUD_ENVIRONMENT", "false").lower() == "true" or not os.path.exists("/var/run/docker.sock")

    if not is_cloud:
        try:
            # PRO MODE: Use Docker Sandbox (Local/Production)
            cmd = ["docker", "run", "--rm", "-v", f"{os.getcwd()}:/workspace", "devloop-sandbox", "pytest", test_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception:
            is_cloud = True # Fallback if Docker fails locally

    # DEMO MODE: Safe Subprocess (Streamlit Cloud Fallback)
    if is_cloud:
        try:
            # Run using the local python interpreter
            result = subprocess.run(["pytest", test_file], capture_output=True, text=True, timeout=10)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Execution Error: {str(e)}"