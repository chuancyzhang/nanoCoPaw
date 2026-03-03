import shutil
import subprocess


def run_command(command: str, cwd: str | None = None, timeout: int = 60) -> str:
    """Run a shell or bash command and return stdout/stderr."""
    bash = shutil.which("bash")
    if bash:
        proc = subprocess.run(
            [bash, "-lc", command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    else:
        proc = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True,
        )
    out = proc.stdout or ""
    err = proc.stderr or ""
    return f"exit={proc.returncode}\nstdout:\n{out}\nstderr:\n{err}"
