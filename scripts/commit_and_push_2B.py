"""commit_and_push_2B.py — Commit y push de Salida 2B. Idempotente."""
import subprocess
import sys
import os


def run(cmd, check=False):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f"FATAL: {cmd}\n{r.stderr}", file=sys.stderr)
        sys.exit(r.returncode)
    return r


def main():
    files = [
        "external/api/capa_api.py",
        "chat-router/chat/ui/loop.js",
        "chat-router/chat/index.html",
        "external/core/SATELITE_CENTRAL_CONECCION.json",
        "scripts/patch_index_html.py",
    ]
    for f in files:
        if os.path.exists(f):
            run(f"git add '{f}'")
            print(f"[git add] {f}")
        else:
            print(f"[SKIP] {f} no existe")

    msg = (
        "infra(2B): capa_api + loop.js + index sessionStorage + central_config\n\n"
        "Deployed-by: Claude-Code · Source: minimax-3-gh-v4B · capa-loop-index-central"
    )
    c = run(f'git commit -m "{msg}"')
    if c.returncode != 0:
        out = (c.stdout + c.stderr).lower()
        if "nothing to commit" in out:
            print("[SKIP] sin cambios pendientes.")
            return
        print(f"FATAL commit: {c.stderr}", file=sys.stderr)
        sys.exit(1)

    p = run("git push origin ccr-f01c3de9-bmry0s", check=True)
    print("[push] OK")

    sha = run("git rev-parse HEAD").stdout.strip()
    print(f"\nCOMMIT: {sha}")
    print(f"URL: https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/{sha}")


if __name__ == "__main__":
    main()
