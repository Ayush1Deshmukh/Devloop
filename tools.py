"""Execution tools for the DevLoop agent.

Two execution backends, picked automatically:

1. Docker sandbox  — used locally / via docker-compose. Strongest isolation.
2. rlimit sandbox  — used on free hosting (Streamlit Cloud, Hugging Face Spaces,
                     Render), where /var/run/docker.sock is never available.

The rlimit backend is not a container, but it is not "just subprocess" either:
generated code runs in a throwaway directory, under CPU/memory/process/file-size
limits, with a wall-clock timeout, and with a scrubbed environment so it cannot
read the API key out of os.environ.
"""

import os
import shutil
import subprocess
import sys
import tempfile

try:
    import resource  # Unix only; absent on Windows.
except ImportError:  # pragma: no cover - Windows fallback
    resource = None

# Exit codes Docker uses when the CLI/daemon/container is the problem, rather
# than the command we asked it to run.
DOCKER_ERROR_CODES = {125, 126, 127}

SANDBOX_CONTAINER = os.getenv("SANDBOX_CONTAINER_NAME", "devloop-sandbox")

# --- rlimit sandbox budget (tuned for a 1GB free-tier container) ---
CPU_SECONDS = int(os.getenv("DEVLOOP_SANDBOX_CPU", "10"))
MEMORY_BYTES = int(os.getenv("DEVLOOP_SANDBOX_MEM_MB", "512")) * 1024 * 1024
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_PROCESSES = 64

# Anything secret must never reach generated code. We rebuild the environment
# from scratch rather than filtering, so a newly added secret cannot leak by
# being forgotten in a denylist.
_ENV_ALLOWLIST = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT")


def _resolve(path):
    """Resolves a path inside the working directory, refusing to escape it."""
    workspace = os.path.realpath(os.getcwd())
    filepath = os.path.realpath(os.path.join(workspace, path))
    if os.path.commonpath([filepath, workspace]) != workspace:
        raise ValueError(f"Refusing to write outside the workspace: {path}")
    return filepath


def write_file(path, content):
    with open(_resolve(path), "w", encoding="utf-8") as f:
        f.write(content)


def _result(completed):
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    if completed.returncode == 0:
        return {"status": "success", "output": output}
    return {"status": "failed", "output": output}


def _safe_env():
    env = {k: os.environ[k] for k in _ENV_ALLOWLIST if k in os.environ}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Keep the app's own packages importable (pytest lives there) without
    # handing over the working directory.
    env["PYTHONPATH"] = ""
    return env


def _apply_rlimits():  # pragma: no cover - runs in the forked child
    """Caps the child's resources. Best-effort: some limits are unavailable
    depending on platform/kernel, and a failure to set one must not stop the run.

    Platform note: macOS accepts RLIMIT_AS but does not enforce it, so the memory
    cap is a no-op there. Linux enforces it, and every free host this deploys to
    (Streamlit Cloud, Hugging Face Spaces, Render) is Linux. The wall-clock
    timeout and RLIMIT_CPU are enforced everywhere, so a runaway process is
    always stopped regardless of platform.
    """
    if resource is None:
        return
    for name, limit in (
        ("RLIMIT_CPU", (CPU_SECONDS, CPU_SECONDS + 2)),
        ("RLIMIT_AS", (MEMORY_BYTES, MEMORY_BYTES)),
        ("RLIMIT_DATA", (MEMORY_BYTES, MEMORY_BYTES)),
        ("RLIMIT_FSIZE", (MAX_FILE_BYTES, MAX_FILE_BYTES)),
        ("RLIMIT_NPROC", (MAX_PROCESSES, MAX_PROCESSES)),
        ("RLIMIT_CORE", (0, 0)),
    ):
        try:
            resource.setrlimit(getattr(resource, name), limit)
        except (ValueError, OSError, AttributeError):
            pass


# --------------------------------------------------------------------------
# Backend 1: Docker
# --------------------------------------------------------------------------
def _sandbox_available():
    """Checks the sandbox container is actually running.

    Docker exits 1 both when the daemon is unreachable and when pytest reports
    failing tests, so the exit code alone cannot tell those apart. We probe
    first: only if the container is confirmed up do we trust the test verdict.
    """
    try:
        completed = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", SANDBOX_CONTAINER],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def _run_in_sandbox(test_file, timeout=30):
    """Runs pytest inside the sandbox container.

    Returns None if the sandbox is unreachable, so the caller can fall back.
    """
    if not _sandbox_available():
        return None

    cmd = ["docker", "exec", SANDBOX_CONTAINER, "pytest", test_file, "-p", "no:cacheprovider"]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, OSError):
        return None
    except subprocess.TimeoutExpired:
        return {"status": "failed", "output": f"Test execution timed out after {timeout}s."}

    if completed.returncode in DOCKER_ERROR_CODES:
        # Container died between the probe and the exec — not a test failure.
        return None
    return _result(completed)


# --------------------------------------------------------------------------
# Backend 2: rlimit sandbox (free hosting)
# --------------------------------------------------------------------------
def _run_with_rlimits(solution_file, test_file, timeout=30):
    """Runs the generated tests in a throwaway dir under resource limits."""
    workdir = tempfile.mkdtemp(prefix="devloop-run-")
    try:
        for name in (solution_file, test_file):
            if os.path.exists(name):
                shutil.copy(name, os.path.join(workdir, os.path.basename(name)))

        popen_kwargs = {}
        if resource is not None and os.name == "posix":
            popen_kwargs["preexec_fn"] = _apply_rlimits

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", os.path.basename(test_file),
                 "-p", "no:cacheprovider", "-q"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workdir,
                env=_safe_env(),
                **popen_kwargs,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "output": (
                    f"Test execution exceeded the {timeout}s wall-clock limit and was "
                    "killed. The generated code is probably blocking or looping."
                ),
            }
        except (OSError, ValueError) as e:
            return {"status": "error", "output": f"Could not start the test runner: {e}"}

        result = _result(completed)
        if completed.returncode == -24:  # SIGXCPU
            result["output"] += f"\n[sandbox] Killed after exceeding {CPU_SECONDS}s of CPU time."
        elif completed.returncode == -9:  # SIGKILL, usually the memory cap
            result["output"] += "\n[sandbox] Killed — exceeded the memory limit."
        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def run_test(solution_file="solution.py", test_file="test_solution.py", timeout=30):
    """Executes the generated tests using the best available isolation.

    Returns {"status": "success" | "failed" | "error", "output": str}.
    "error" means the runner itself broke and the result says nothing about the
    generated code — callers must not feed it back to the LLM as a test failure.
    """
    if os.getenv("DEVLOOP_FORCE_LOCAL_TESTS") != "1":
        sandbox_result = _run_in_sandbox(test_file, timeout=timeout)
        if sandbox_result is not None:
            return sandbox_result

    return _run_with_rlimits(solution_file, test_file, timeout=timeout)


def sandbox_backend():
    """Reports which execution backend a run would actually use.

    The UI surfaces this so nobody has to guess whether generated code is being
    isolated in a container or merely rlimited on the host — the two have very
    different security properties, and the difference used to be invisible.
    """
    if os.getenv("DEVLOOP_FORCE_LOCAL_TESTS") == "1":
        return "rlimit"
    return "docker" if _sandbox_available() else "rlimit"
