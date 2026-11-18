"""commit_minimax3.py — Commit y push de los 3 archivos generados por MiniMax 3."""
import subprocess, sys


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(r.returncode)


def main():
    run(["git", "add",
         "router_llm_hf/SATELITE_CENTRAL_CONECCION.json",
         "router_llm_hf/mode_detector.py",
         "router_llm_hf/mode_router.py",
         "scripts/centralize_registry.py",
         "scripts/gen_mode_detector.py",
         "scripts/gen_mode_router.py",
         "scripts/commit_minimax3.py"])
    run(["git", "commit", "-m",
         "feat(mode): registro central + detector 12 modos (IGNORECASE) + mode_router cableado"])
    run(["git", "push", "origin", "ccr-f01c3de9-bmry0s"])


if __name__ == "__main__":
    main()
