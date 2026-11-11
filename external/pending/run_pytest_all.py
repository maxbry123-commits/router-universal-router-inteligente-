"""
run_pytest_all.py — Ejecuta todos los tests del repo (cierra F5)
Ubicacion: external/pending/run_pytest_all.py
Uso: python external/pending/run_pytest_all.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_DIRS = [
    ROOT / "ROUTER MVP v1" / "system_prompt_py" / "tests",
    ROOT / "router_llm_hf" / "tests",
]


def run_one(test_dir: Path) -> dict:
    result = {"dir": str(test_dir), "exists": test_dir.exists(), "files": [], "rc": None}
    if not result["exists"]:
        return result
    files = sorted(p.name for p in test_dir.glob("test_*.py"))
    result["files"] = files
    if not files:
        return result
    cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result["rc"] = proc.returncode
    result["stdout"] = proc.stdout[-2000:]
    result["stderr"] = proc.stderr[-2000:]
    return result


def main():
    results = [run_one(d) for d in TEST_DIRS]
    print("=" * 70)
    print("REPORTE DE TESTS")
    print("=" * 70)
    all_ok = True
    for r in results:
        print(f"\n[{r['dir']}]")
        if not r["exists"]:
            print("  NO EXISTE (skip)")
            continue
        if not r["files"]:
            print("  sin test_*.py (skip)")
            continue
        print(f"  archivos: {r['files']}")
        print(f"  rc: {r['rc']}")
        if r["rc"] != 0:
            all_ok = False
        if r.get("stdout"):
            print("  --- stdout ---")
            print(r["stdout"])
        if r.get("stderr"):
            print("  --- stderr ---")
            print(r["stderr"])
    print("=" * 70)
    print("RESULTADO FINAL:", "OK" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
