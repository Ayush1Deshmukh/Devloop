import subprocess
import os
import sys


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def run_test(filename="solution.py", test_file="test_solution.py"):
    # Check if we are in the cloud (Streamlit Cloud environment)
    is_cloud = os.getenv("STREAMLIT_CLOUD_ENVIRONMENT") == "true" or not os.path.exists("/var/run/docker.sock")

    if is_cloud:
        # CLOUD MODE: Use local Python (Required for Streamlit Cloud)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file], 
                capture_output=True, text=True, timeout=15
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Cloud Execution Error: {str(e)}"
    else:
        # LOCAL MODE: Use Docker Sandbox (For your MacBook)
        try:
            cmd = ["docker", "run", "--rm", "-v", f"{os.getcwd()}:/workspace", "devloop-sandbox", "pytest", test_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Docker Sandbox Error: {str(e)}"