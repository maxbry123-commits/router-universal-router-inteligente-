"""
registry_fill_runner.py — Calcula sha256 reales de GGUF (cierra O7)
Ubicacion: external/pending/registry_fill_runner.py
Uso: python external/pending/registry_fill_runner.py [registry.json path]
"""
import hashlib
import json
import os
import sys
from pathlib import Path


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fill_registry(registry_path: str, dry_run: bool = False) -> dict:
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    models = reg.setdefault("models", {})
    report = []
    for space, entry in models.items():
        path = entry.get("model_path")
        current_sha = entry.get("sha256")
        if not path or not os.path.exists(path):
            report.append({"space": space, "status": "missing_file", "path": path})
            continue
        actual = sha256_file(path)
        if not current_sha:
            entry["sha256"] = actual
            report.append({"space": space, "status": "filled", "sha256": actual})
        elif current_sha == actual:
            report.append({"space": space, "status": "ok", "sha256": actual})
        else:
            report.append({
                "space": space,
                "status": "mismatch",
                "expected": current_sha,
                "actual": actual,
            })
    if not dry_run:
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2, ensure_ascii=False)
    return {"dry_run": dry_run, "report": report}


def main():
    default_path = (
        Path(__file__).resolve().parents[2]
        / "llm system HF"
        / "registry.json"
    )
    path = sys.argv[1] if len(sys.argv) > 1 else str(default_path)
    dry_run = "--dry-run" in sys.argv
    print(f"Registry: {path}")
    print(f"Dry-run:  {dry_run}")
    if not os.path.exists(path):
        print("NO EXISTE (crea el registry con Salida 1/3 HF primero)")
        return 1
    result = fill_registry(path, dry_run=dry_run)
    for r in result["report"]:
        print(f"  {r['space']}: {r['status']}")
        if r["status"] == "mismatch":
            print(f"    expected: {r['expected']}")
            print(f"    actual:   {r['actual']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
