"""shell_tool.py - Wrapper de sandbox.run con parseo de comando."""
import shlex
from router_llm_hf.sandbox import run as _run

def run_shell(cmd: str, timeout: int = 30, cwd: str = None) -> dict:
    try:
        argv = shlex.split(cmd)
    except Exception as e:
        return {"ok": False, "error": f"parse:{e}"}
    return _run(argv, timeout=timeout, cwd=cwd)
