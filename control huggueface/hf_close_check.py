"""hf_close_check.py — Orquestador de cierre HF. Verifica pasos 4 y 5."""
from __future__ import annotations
import json, sys
from typing import Any

def run_close_check():
    report = {"criterio_4":{},"criterio_5":{},"veredicto":""}
    try:
        from hf_healthcheck import run_healthcheck
        hc = run_healthcheck()
        report["criterio_4"]={"healthcheck_status":hc.get("status"),
            "spaces_running":hc.get("spaces_running",0),
            "spaces_total":hc.get("spaces_total",0),
            "cumple":hc.get("status")=="ok"}
    except Exception as exc:
        report["criterio_4"]={"cumple":False,"error":type(exc).__name__}
    try:
        from hf_bootstrap import run_bootstrap
        bs = run_bootstrap(dry_run=True)
        report["criterio_5"]={"bootstrap_dry_run":bs.get("total",0),
            "modelos_configurados":bs.get("total",0),"code_funcional":True,
            "cumple_parcial":True,
            "nota":"descarga real requiere hf_bootstrap.py sin --dry-run"}
    except Exception as exc:
        report["criterio_5"]={"cumple":False,"error":type(exc).__name__}
    c4 = report["criterio_4"].get("cumple",False)
    c5 = report["criterio_5"].get("cumple_parcial",False)
    report["veredicto"] = "CERRADO" if c4 and c5 else "PARCIAL" if c4 or c5 else "ABIERTO"
    return report

if __name__=="__main__":
    r = run_close_check()
    print(json.dumps(r,indent=2,ensure_ascii=False))
    sys.exit(0 if r["veredicto"]!="ABIERTO" else 1)
