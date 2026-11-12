import subprocess
import time

def execute_code_safely(cmd: list, project_root: str, timeout_s: int = 300) -> dict:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "TIMEOUT", "elapsed_s": timeout_s}

    logs = completed.stdout + "\n" + completed.stderr

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "elapsed_s": round(time.monotonic() - started, 2),
        "logs": logs[-3000:]
    }
