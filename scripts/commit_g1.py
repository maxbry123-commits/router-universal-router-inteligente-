"""commit_g1.py — Commit y push del fixer G1."""
import subprocess, sys
def run(cmd):
    print("$ " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0: print(r.stderr); sys.exit(r.returncode)
if __name__ == "__main__":
    run(["git", "add", "scripts/hf_verify_and_fix_port_v2v7.py", "scripts/commit_g1.py"])
    run(["git", "commit", "-m", "fix(port): app_port:7860 en v2/v7 READMEs"])
    run(["git", "push", "origin", "ccr-f01c3de9-bmry0s"])
