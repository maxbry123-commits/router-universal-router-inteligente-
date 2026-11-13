"""hf_deploy_check.py — Orquestador de despliegue HF completo."""
from __future__ import annotations
import argparse, json, sys
from typing import Any

def run_deploy_check(namespace, skip_download=False):
    report = {"namespace":namespace,"setup":{},"bootstrap":{},"healthcheck":{},
              "criterio_4":False,"criterio_5":False,"veredicto":"ABIERTO"}
    try:
        from hf_setup_spaces import run_setup
        report["setup"] = run_setup(namespace)
    except Exception as exc:
        report["setup"] = {"error":type(exc).__name__+": "+str(exc)[:200]}
    if not skip_download:
        try:
            from hf_bootstrap import run_bootstrap
            report["bootstrap"] = run_bootstrap(dry_run=False)
        except Exception as exc:
            report["bootstrap"] = {"error":type(exc).__name__+": "+str(exc)[:200]}
    else:
        report["bootstrap"] = {"skipped":True}
    try:
        from hf_healthcheck import run_healthcheck
        report["healthcheck"] = run_healthcheck(namespace)
    except Exception as exc:
        report["healthcheck"] = {"error":type(exc).__name__+": "+str(exc)[:200]}
    setup_ok = report["setup"].get("spaces_ok",0)==report["setup"].get("spaces_total",3)
    hc = report["healthcheck"]
    hc_ok = hc.get("status")=="ok" if isinstance(hc,dict) else False
    bs = report["bootstrap"]
    bs_ok = bs.get("descargados",0)==bs.get("total",3) if isinstance(bs,dict) else False
    report["criterio_4"] = setup_ok and hc_ok
    report["criterio_5"] = bs_ok
    if report["criterio_4"] and report["criterio_5"]:
        report["veredicto"] = "CERRADO"
    elif report["criterio_4"] or report["criterio_5"]:
        report["veredicto"] = "PARCIAL"
    return report

if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--skip-download", action="store_true")
    a = ap.parse_args()
    r = run_deploy_check(a.namespace, skip_download=a.skip_download)
    print(json.dumps(r,indent=2,ensure_ascii=False))
    sys.exit(0 if r["veredicto"]=="CERRADO" else 1)
