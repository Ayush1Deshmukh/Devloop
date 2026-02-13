import subprocess
import os


WORKSPACE_DIR = os.getcwd()

def write_file(filename: str, content: str):
    """Writes content to a file in the workspace."""
    filepath = os.path.join(WORKSPACE_DIR, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return f"Successfully wrote to {filename}"

def run_test(test_filename: str):
   def run_test(test_filename: str):
    """Executes pytest inside the Sandbox Docker container."""
    # Get container name from env (default to devloop-sandbox)
    container_name = os.getenv("SANDBOX_CONTAINER_NAME", "devloop-sandbox")
    
    # We execute the test inside the sandbox container
    cmd = ["docker", "exec", container_name, "pytest", test_filename]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"status": "failed", "output": result.stdout + "\n" + result.stderr}
    except Exception as e:
        return {"status": "error", "output": str(e)}