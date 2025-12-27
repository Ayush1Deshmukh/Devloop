import subprocess

# The name of our running Docker container
CONTAINER_NAME = "devloop-runner"

def write_file(filename: str, content: str):
    """
    Writes content to a file on your Mac.
    Since we mounted $(pwd) to /app, the Docker container 
    will instantly see these files too.
    """
    with open(filename, "w") as f:
        f.write(content)
    return f"Successfully wrote to {filename}"

def run_test(test_filename: str):
    """
    Executes pytest INSIDE the Docker container.
    """
    # This command runs pytest inside the 'devloop-runner' container
    cmd = ["docker", "exec", CONTAINER_NAME, "pytest", test_filename]
    
    try:
        # Run the docker command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10 
        )
        
        # Docker exit code 0 means tests passed
        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            # Tests failed. Return stdout + stderr so the AI knows WHY.
            return {"status": "failed", "output": result.stdout + "\n" + result.stderr}
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Test Execution Timed Out (Possible Infinite Loop)"}
    except Exception as e:
        return {"status": "error", "output": str(e)}