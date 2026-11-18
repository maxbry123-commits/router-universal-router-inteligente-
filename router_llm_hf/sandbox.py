"""sandbox.py - Subprocess aislado con timeout y allowlist de binarios."""
import os, shutil, subprocess

ALLOWLIST = set(os.getenv(
    "SANDBOX_ALLOWLIST",
    "python,python3,pytest,ruff,mypy,node,npm,git,ls,cat,grep,find,pwd,echo"
).split(","))
MAX_TIMEOUT = int(os.getenv("SANDBOX_MAX_TIMEOUT", "60"))

def _check_bin(cmd: list) -> str | None:
    if not cmd: return "empty_cmd"
    b = os.path.basename(cmd[0])
    if b not in ALLOWLIST: return f"binary_not_allowed:{b}"
    if not shutil.which(b): return f"binary_not_found:{b}"
    return None

def run(cmd: list, timeout: int = 30, cwd: str = None) -> dict:
    err = _check_bin(cmd)
    if err: return {"ok": False, "error": err}
    if timeout > MAX_TIMEOUT: timeout = MAX_TIMEOUT
    env = {"PATH": os.getenv("PATH", ""),
           "HOME": os.getenv("HOME", "/tmp"),
           "LANG": "C.UTF-8"}
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd, env=env)
        return {"ok": r.returncode == 0, "rc": r.returncode,
                "stdout": r.stdout[-10_000:], "stderr": r.stderr[-10_000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "timeout": timeout}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}
