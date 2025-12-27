import subprocess
import shutil
import sys

# Check if Docker is available on the system
HAS_DOCKER = shutil.which("docker") is not None

def write_file(filename: str, content: str):
    """
    Writes content to a file on your Mac.
    Since we mounted $(pwd) to /app, the Docker container 
    will instantly see these files too.
    """
    with open(filename, "w") as f:
        f.write(content)
    return f"Saved {filename}"

def run_test(test_filename: str):
    """
    Smart Runner: Uses Docker if available (Local),
    falls back to direct execution if not (Cloud Demo).
    """
    if HAS_DOCKER:
        # Secure Local Mode
        cmd = ["docker", "exec", "devloop-runner", "pytest", test_filename]
    else:
        # Cloud Demo Mode (Runs directly on Streamlit Cloud VM)
        cmd = [sys.executable, "-m", "pytest", test_filename]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        status = "success" if result.returncode == 0 else "failed"
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
            
        return {"status": status, "output": output}
            
    except Exception as e:
        return {"status": "error", "output": str(e)}