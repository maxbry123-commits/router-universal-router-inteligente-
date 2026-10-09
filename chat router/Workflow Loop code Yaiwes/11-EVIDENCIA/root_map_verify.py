"""T11-G — verifica que cada ruta del ROOT-MAP existe (read-back físico).
Uso: python "chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/root_map_verify.py"
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "chat router/Workflow Loop code Yaiwes/01-PLAN/ROOT-MAP-T11.yaml"


def verify(root: Path = ROOT) -> dict:
    data = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    report = {"schema": data["schema"], "roots": [], "ok": True}
    for r in data["roots"]:
        paths = [{"path": p, "status": "VERIFIED" if (root / p).exists() else "MISSING"}
                 for p in r["paths"]]
        missing = [p["path"] for p in paths if p["status"] == "MISSING"]
        if missing:
            report["ok"] = False
        report["roots"].append({"id": r["id"], "name": r["name"], "paths": paths, "missing": missing})
    return report


def main() -> int:
    report = verify()
    ok = report["ok"]
    for r in report["roots"]:
        print(f"ROOT {r['id']} {r['name']}: {len(r['paths'])} paths, missing={r['missing']}")
    print("ROOT-MAP-T11", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
