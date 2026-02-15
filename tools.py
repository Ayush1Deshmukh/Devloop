import subprocess
import os
import sys

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def run_test(solution_file="solution.py", test_file="test_solution.py"):
    # Streamlit Cloud Detection
    is_cloud = os.getenv("STREAMLIT_CLOUD_ENVIRONMENT") == "true" or not os.path.exists("/var/run/docker.sock")

    if is_cloud:
        # CLOUD MODE (Subprocess)
        try:
            # We use sys.executable to ensure we use the same python environment
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file], 
                capture_output=True, text=True, timeout=15
            )
            status = "success" if result.returncode == 0 else "failed"
            return {"status": status, "output": result.stdout + result.stderr}
        except Exception as e:
            return {"status": "error", "output": str(e)}
    else:
        # LOCAL MODE (Docker)
        try:
            # Assumes you have a docker image named 'devloop-sandbox'
            # If not, it falls back to subprocess nicely
            cmd = ["docker", "run", "--rm", "-v", f"{os.getcwd()}:/workspace", "devloop-sandbox", "pytest", test_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            status = "success" if result.returncode == 0 else "failed"
            return {"status": status, "output": result.stdout + result.stderr}
        except Exception:
            # Fallback if Docker fails locally
            result = subprocess.run([sys.executable, "-m", "pytest", test_file], capture_output=True, text=True)
            status = "success" if result.returncode == 0 else "failed"
            return {"status": status, "output": result.stdout + result.stderr}