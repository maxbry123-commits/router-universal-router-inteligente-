"""commit_g2.py — Commit y push del runner G2 (mismo patron que commit_g1)."""
import subprocess, sys
def run(cmd):
    print("$ " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0: print(r.stderr); sys.exit(r.returncode)
if __name__ == "__main__":
    run(["git", "add", "scripts/oauth_setup_runner.py", "docs/OAUTH_SETUP.md", "scripts/commit_g2.py",
         "router/banco/hf/secrets.json"])
    run(["git", "commit", "-m", "feat(oauth): escaner de los 5 MCP OAuth + URLs en el banco"])
    run(["git", "push", "origin", "ccr-f01c3de9-bmry0s"])
