import os
import subprocess

WORKSPACE_DIR = os.getcwd()

# `docker` itself reports these when the CLI/daemon/container is the problem,
# rather than the command we asked it to run. Treated as infrastructure errors,
# never as "the generated code failed its tests".
DOCKER_ERROR_CODES = {125, 126, 127}


def _resolve(filename: str) -> str:
    """Resolves a filename inside the workspace, refusing to escape it."""
    filepath = os.path.realpath(os.path.join(WORKSPACE_DIR, filename))
    workspace = os.path.realpath(WORKSPACE_DIR)
    if os.path.commonpath([filepath, workspace]) != workspace:
        raise ValueError(f"Refusing to access path outside the workspace: {filename}")
    return filepath


def write_file(filename: str, content: str):
    """Writes content to a file in the workspace."""
    filepath = _resolve(filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote to {filename}"


def _sandbox_running(container_name: str) -> bool:
    """Checks the sandbox container is up.

    Docker exits 1 both when the daemon is unreachable and when pytest reports
    failing tests, so the exit code alone cannot tell those apart. Probe first;
    only if the container is confirmed up do we trust the test verdict.
    """
    try:
        completed = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def run_test(test_filename: str, timeout: int = 30):
    """Executes pytest inside the Sandbox Docker container.

    Returns a dict with:
      status: "success" | "failed" | "error"
      output: combined stdout/stderr

    "error" means the sandbox itself could not be reached (Docker down, container
    not running). Callers must NOT feed that back to the LLM as a test failure —
    it would loop forever trying to "fix" perfectly good code.
    """
    container_name = os.getenv("SANDBOX_CONTAINER_NAME", "devloop-sandbox")

    if not _sandbox_running(container_name):
        return {
            "status": "error",
            "output": f"Sandbox container '{container_name}' is not running.",
        }

    cmd = ["docker", "exec", container_name, "pytest", test_filename]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return {"status": "error", "output": "Docker CLI not found — cannot reach the sandbox."}
    except subprocess.TimeoutExpired:
        return {"status": "failed", "output": f"Test execution timed out after {timeout}s."}
    except Exception as e:  # noqa: BLE001 - surfaced to the caller as an infra error
        return {"status": "error", "output": str(e)}

    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")

    if result.returncode == 0:
        return {"status": "success", "output": output}
    if result.returncode in DOCKER_ERROR_CODES:
        return {"status": "error", "output": f"Sandbox unavailable (exit {result.returncode}):\n{output}"}
    return {"status": "failed", "output": output}
