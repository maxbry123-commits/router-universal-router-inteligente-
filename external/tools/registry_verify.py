"""
registry_verify.py — Verifica registry.json contra modelos reales del disco
Ubicacion: external/tools/registry_verify.py
Uso: python external/tools/registry_verify.py [registry.json path]
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


def verify(registry_path: str) -> dict:
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    results = []
    for space, entry in reg.get("models", {}).items():
        path = entry.get("model_path")
        expected = entry.get("sha256")
        if not path:
            results.append({"space": space, "status": "no_path"})
            continue
        if not os.path.exists(path):
            results.append({"space": space, "status": "missing_file", "path": path})
            continue
        actual = sha256_file(path)
        if not expected:
            results.append({"space": space, "status": "sha256_null", "actual": actual})
        elif expected == actual:
            results.append({"space": space, "status": "ok", "sha256": actual})
        else:
            results.append({
                "space": space,
                "status": "mismatch",
                "expected": expected,
                "actual": actual,
            })
    return results


def main():
    default = (
        Path(__file__).resolve().parents[2]
        / "llm system HF"
        / "registry.json"
    )
    path = sys.argv[1] if len(sys.argv) > 1 else str(default)
    print(f"Registry: {path}")
    if not os.path.exists(path):
        print("NO EXISTE")
        return 1
    results = verify(path)
    for r in results:
        print(f"  {r['space']}: {r['status']}")
        if r["status"] == "mismatch":
            print(f"    expected: {r['expected'][:16]}...")
            print(f"    actual:   {r['actual'][:16]}...")
    all_ok = all(r["status"] == "ok" for r in results)
    print(f"\nRESULTADO: {'OK' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
