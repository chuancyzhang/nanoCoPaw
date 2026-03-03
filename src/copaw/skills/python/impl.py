import subprocess
import sys


def run_python(code: str, cwd: str | None = None, timeout: int = 60) -> str:
    """Run a Python code snippet with the current interpreter."""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = proc.stdout or ""
    err = proc.stderr or ""
    return f"exit={proc.returncode}\nstdout:\n{out}\nstderr:\n{err}"
