#!/usr/bin/env python3
"""commit_minimax_2e.py — Commit + push determinista de la Salida 2E (MINIMAX 4).

MEJORAS frente a los scripts del owner (commit_v5.py / commit_minimax3.py):
  · FAIL-CLOSED: ejecuta scripts/validate_2e.py ANTES de commitear; si algo
    falla, no hay commit.
  · `git add --sparse`: el clon es sparse y `git add` de rutas fuera del cono
    falla silenciosamente (el stderr se descarta) -> ficheros que se quedan
    sin commitear sin que nadie se entere.
  · PUSH CON CREDENCIALES: los scripts del owner hacen `git push` sin helper y
    el push muere con "could not read Username for https://github.com". Aqui el
    token va por variable de entorno ($GH_TOKEN), nunca en el comando ni en el log.
  · VERIFICACION POST-PUSH: compara el sha remoto con el local (comparacion
    EXACTA; `git ls-remote <url> <sha>` es fail-open y no vale como gate).
"""
from __future__ import annotations

import os
import subprocess
import sys

BRANCH = "ccr-f01c3de9-bmry0s"
OWNER = "maxbry123-commits"
REPO = "router-universal-router-inteligente-"

FILES = [
    "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py",
    "chat-router/chat/index.html",
    "chat-router/chat/ui/model-selector.js",
    "chat-router/chat/ui/ui-controller.js",
    "chat-router/chat/ui/openclaw-panel.html",
    "chat-router/chat/ui/hermes-panel.html",
    "external/core/storage_wiring.py",
    "router_llm_hf/AGENTS_REGISTRY.json",
    "router_llm_hf/__init__.py",
    "router_llm_hf/agent_router.py",
    "router_llm_hf/chat_ab_orchestrator.py",
    "router_llm_hf/harness_wiring.py",
    "router_llm_hf/loop_engine.py",
    "scripts/hf_restart_space.py",
    "scripts/validate_2e.py",
    "scripts/commit_minimax_2e.py",
]

SUBJECT = "feat(2e): loop+espejo+memoria+harness+agentes"
TRAILER = ("Deployed-by: Claude-Code · Source: minimax-4-gh-2e-v1 · "
           "WIRE_LOOP_MIRROR_MEMORY · cableado del chat, agentes, espejo y memoria")


def run(cmd, check=False):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f"FATAL: {cmd}\n{r.stdout}\n{r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r


def main():
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print("FATAL: falta GH_TOKEN en el entorno", file=sys.stderr)
        return 1

    # 1. Gate de validacion (fail-closed).
    v = run(f"{sys.executable} -B scripts/validate_2e.py")
    print(v.stdout)
    if v.returncode != 0:
        print("FATAL: validacion fallida -> no se commitea", file=sys.stderr)
        return 1

    # 2. Stage (sparse-safe).
    for f in FILES:
        if os.path.exists(f):
            run(f"git add --sparse -- '{f}'")
            print(f"[add] {f}")
        else:
            print(f"[skip] {f} (no existe)")

    # 3. Commit con la convencion de la casa.
    msg = f"{SUBJECT}\n\n{TRAILER}"
    c = run(f'git commit -m "{msg}"')
    if c.returncode != 0:
        if "nothing to commit" in (c.stdout + c.stderr).lower():
            print("IDEMPOTENTE: sin cambios.")
            return 0
        print(f"FATAL commit: {c.stdout} {c.stderr}", file=sys.stderr)
        return 1

    sha = run("git rev-parse HEAD").stdout.strip()
    print(f"\nCOMMIT:{sha}")

    # 4. Push fast-forward con credenciales (nunca force).
    helper = ("!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f")
    p = run(f"git -c credential.helper= -c 'credential.helper={helper}' "
            f"push origin HEAD:refs/heads/{BRANCH}")
    print(p.stdout.strip() or p.stderr.strip())
    if p.returncode != 0:
        print("FATAL push: la rama se movio o fallo la autenticacion", file=sys.stderr)
        return 1

    # 5. Verificacion post-push: sha remoto == sha local (comparacion EXACTA).
    remote = run(f"git ls-remote origin refs/heads/{BRANCH}").stdout.split()
    if not remote or remote[0] != sha:
        print(f"FATAL: sha remoto {remote[:1]} != local {sha}", file=sys.stderr)
        return 1

    st = run("git status --porcelain").stdout.strip()
    print(f"REMOTE_MATCH:{remote[0]}")
    print(f"WORKTREE_CLEAN:{'yes' if not st else 'no -> ' + st}")
    print(f"URL:https://github.com/{OWNER}/{REPO}/commit/{sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
