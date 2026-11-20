"""commit_and_push_2A.py — Commit y push de los archivos de Salida 2A.
Idempotente: si no hay cambios, no falla.
"""
import subprocess
import sys
import os


def run(cmd, check=False):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"FATAL: {cmd}\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def main():
    # Archivos modificados/creados en esta salida
    files = [
        "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py",
        "router_llm_hf/harness_wiring.py",
        "router_llm_hf/checkpoint_manager.py",
        "scripts/patch_proxy_lifespan.py",
    ]

    for f in files:
        if os.path.exists(f):
            run(f"git add '{f}'")
            print(f"[git add] {f}")
        else:
            print(f"[SKIP] {f} no existe")

    # Commit (idempotente: si no hay cambios, git commit falla pero continuamos)
    msg = (
        "infra(2A): patch quirurgico proxy lifespan + loop endpoints + harness + checkpoint\n\n"
        "Deployed-by: Claude-Code · Source: minimax-3-gh-v4A-quirurgico · patch-lifespan-harness-checkpoint"
    )
    commit_result = run(f'git commit -m "{msg}"')
    if commit_result.returncode != 0:
        if "nothing to commit" in commit_result.stdout.lower() or "nothing to commit" in commit_result.stderr.lower():
            print("[SKIP] No hay cambios pendientes. Ya está commiteado.")
            return
        else:
            print(f"FATAL: git commit falló:\n{commit_result.stderr}", file=sys.stderr)
            sys.exit(1)

    # Push
    push_result = run("git push origin ccr-f01c3de9-bmry0s", check=True)
    print("[push] OK")

    # SHA
    sha = run("git rev-parse HEAD").stdout.strip()
    print(f"\nCOMMIT: {sha}")
    print(f"URL: https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/{sha}")


if __name__ == "__main__":
    main()
