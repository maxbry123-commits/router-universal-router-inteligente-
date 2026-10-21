"""Autoactualizador del Router: cada `interval` s hace `git pull --ff-only`; si HEAD cambia, reinicia solo este proceso."""
import os, subprocess, sys, threading, time


def _git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, timeout=120).stdout.strip()


def start(repo_dir=None, interval=60):
    if os.environ.get("ROUTER_AUTOPULL", "1") == "0":
        return None
    repo = repo_dir or _git(os.path.dirname(os.path.abspath(__file__)), "rev-parse", "--show-toplevel")
    if not repo:
        return None

    def loop():
        head = _git(repo, "rev-parse", "HEAD")
        while True:
            time.sleep(interval)
            try:
                _git(repo, "pull", "--ff-only")
                new = _git(repo, "rev-parse", "HEAD")
                if new and new != head:
                    os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception:
                pass

    t = threading.Thread(target=loop, name="router-autopull", daemon=True)
    t.start()
    return t
