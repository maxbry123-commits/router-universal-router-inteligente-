"""Verificador E2E de conectividad para ejecutar dentro del runtime/Codespace.

Uso:
  python verify_runtime_connectivity.py --repo maxbry123-commits/frontend

Nunca imprime valores de tokens. Salida JSON contiene solo nombres de referencias,
identidad, permisos y estados de gates.
"""
from __future__ import annotations

import argparse
import json

from connectivity_runtime import (
    HF_ACCOUNT,
    MissingCredential,
    probe_github,
    probe_github_mcp,
    probe_huggingface,
    public_runtime_status,
)


def run(repo: str) -> tuple[int, dict]:
    report: dict = {
        "schema": "riu.connectivity.verify/v1",
        "repo": repo,
        "runtime": public_runtime_status(),
        "gates": {},
    }

    if report["runtime"]["github"]["status"] != "AVAILABLE":
        report["gates"]["github"] = "PENDING_RUNTIME_CREDENTIAL_VISIBILITY"
    if report["runtime"]["huggingface"]["status"] != "AVAILABLE":
        report["gates"]["huggingface"] = "PENDING_RUNTIME_CREDENTIAL_VISIBILITY"
    if report["gates"]:
        report["status"] = "FAIL_CLOSED"
        return 2, report

    try:
        github = probe_github(repo)
        report["github"] = github
        report["gates"]["github"] = "PASS" if github["status"] == "PASS" else "FAIL"

        huggingface = probe_huggingface()
        report["huggingface"] = huggingface
        hf_ok = huggingface["status"] == "PASS" and huggingface.get("identity") == HF_ACCOUNT
        report["gates"]["huggingface"] = "PASS" if hf_ok else "FAIL_WRONG_ACCOUNT_OR_AUTH"

        mcp = probe_github_mcp()
        report["github_mcp"] = mcp
        report["gates"]["github_mcp"] = "PASS" if mcp["status"] == "PASS" else "FAIL"
    except MissingCredential as exc:
        report["status"] = "FAIL_CLOSED"
        report["error"] = type(exc).__name__
        return 2, report
    except RuntimeError as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        return 1, report

    report["status"] = "PASS" if all(value == "PASS" for value in report["gates"].values()) else "FAIL"
    return (0 if report["status"] == "PASS" else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="maxbry123-commits/router-universal-router-inteligente-")
    args = parser.parse_args()
    code, report = run(args.repo)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
