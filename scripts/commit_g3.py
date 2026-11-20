"""commit_g3.py — push de la branch fix/remove-riu-router (no merge a main)."""
import subprocess, sys
def run(cmd):
    print("$ " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0: print(r.stderr); sys.exit(r.returncode)
if __name__ == "__main__":
    run(["git", "push", "origin", "fix/remove-riu-router"])
