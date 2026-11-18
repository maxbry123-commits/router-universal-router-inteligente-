"""commit_v5.py - Commit + push determinista de Salida 2D/4."""
import os, subprocess, sys

FILES = [
    "external/tools/fs_tools.py", "router_llm_hf/sandbox.py",
    "external/tools/shell_tool.py", "external/tools/tool_registry.py",
    "external/tools/verify_tool.py", "external/core/context_manager.py",
    "external/core/semantic_cache.py", "external/history/conversation_store.py",
    "external/memory/long_term.py", "external/core/health_check.py",
    "scripts/hf_validate_secrets.py", "scripts/hf_verify_adapters.py",
    "scripts/patch_fix3_modes.py", "scripts/patch_loop_resume.py",
    "scripts/apply_improvements_v5.py",
    "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py",
    "router_llm_hf/mode_router.py", "router_llm_hf/harness_wiring.py",
    "router_llm_hf/checkpoint_manager.py", "external/api/capa_api.py",
    "chat-router/chat/ui/loop.js", "scripts/hf_restart_space.py",
    "external/core/SATELITE_CENTRAL_CONECCION.json",
    "reports/adapters_verify.json",
]


def run(c, check=False):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f"FATAL:{c}\n{r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r


def main():
    for f in FILES:
        if os.path.exists(f):
            run(f"git add '{f}'")
            print(f"[add] {f}")
    msg = ("infra(2D): tools+memoria+context+cache+health+modos GAP+8 mejoras\n\n"
           "Deployed-by: Claude-Code · Source: minimax-4-gh-v5-final-r2 · env-programmable")
    c = run(f'git commit -m "{msg}"')
    if c.returncode != 0:
        if "nothing to commit" in (c.stdout + c.stderr).lower():
            print("IDEMPOTENTE: sin cambios."); return
        print(f"FATAL:{c.stderr}", file=sys.stderr); sys.exit(1)
    run("git push origin ccr-f01c3de9-bmry0s", check=True)
    sha = run("git rev-parse HEAD").stdout.strip()
    print(f"\nCOMMIT:{sha}")
    print(f"URL:https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/{sha}")


if __name__ == "__main__":
    main()
