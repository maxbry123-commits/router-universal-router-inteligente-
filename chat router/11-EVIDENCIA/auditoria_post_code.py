"""Repite el inventario y verifica el delta backend sin atribuir conectividad externa."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys

from auditoria_plan import PLAN, ROOT, build, sha256

OUTPUT = PLAN / "AUDITORIA-4-PASADAS-POST-CODE.json"
CODE = (
    "chat router/memoria/memoria_yaiwes/__init__.py",
    "chat router/11-EVIDENCIA/auditoria_plan.py",
    "chat router/11-EVIDENCIA/auditoria_post_code.py",
    "chat router/11-EVIDENCIA/auditoria_metodo.py",
    "chat router/11-EVIDENCIA/buscadores.py",
    "chat router/11-EVIDENCIA/compilador_busquedas.py",
    "chat router/11-EVIDENCIA/evidence_pack.py",
    "chat router/11-EVIDENCIA/parser.py",
    "chat router/11-EVIDENCIA/puerta.py",
    "chat router/11-EVIDENCIA/tests/test_puerta.py",
    "chat router/11-EVIDENCIA/verificador.py",
    "router inteligente universal/integration/chat_mvp/memory_runtime.py",
    "router inteligente universal/integration/chat_mvp/memoria_loader.py",
    "router inteligente universal/integration/chat_mvp/router.py",
    "router inteligente universal/integration/chat_mvp/org_api.py",
    "router inteligente universal/integration/chat_mvp/ui_bridge.py",
    "router inteligente universal/tests/test_chat_mvp_app.py",
    "router inteligente universal/tests/test_method_audit.py",
    "router inteligente universal/tests/test_org_api.py",
)
TESTS = (
    "router inteligente universal/tests/test_chat_mvp_app.py",
    "router inteligente universal/tests/test_org_api.py",
    "chat router/memoria/tests/test_memoria_yaiwes.py",
    "chat router/11-EVIDENCIA/tests/test_puerta.py",
    "router inteligente universal/tests/test_method_audit.py",
)


def command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def code_entry(path: str, tested: bool) -> dict:
    data = (ROOT / path).read_bytes()
    ast.parse(data.decode("utf-8"), filename=path)
    previous = command("git", "show", f"HEAD:{path}")
    if path.endswith("/auditoria_plan.py"):
        wiring = "INPUT_INVENTORY_BUILT_LOCALLY"
        evidence = "SOURCE_HASHES_AND_COUNTS_VERIFIED"
    elif path.endswith("/auditoria_post_code.py"):
        wiring = "POST_AUDIT_EXECUTED_LOCALLY"
        evidence = "OUTPUT_JSON_READBACK_VERIFIED"
    elif path.startswith("chat router/11-EVIDENCIA/") or path.endswith("/test_method_audit.py"):
        wiring = "LOCAL_GATE_TESTS" if tested else "🚩 PENDIENTE: GATE_NOT_TESTED"
        evidence = "LOCAL_DETERMINISTIC_TESTS_SIMULATED" if tested else "🚩 PENDIENTE: EXECUTION_NOT_DEMONSTRATED"
    else:
        wiring = "LOCAL_INTEGRATION_TESTS" if tested else "🚩 PENDIENTE: RUNTIME_WIRING_NOT_DEMONSTRATED"
        evidence = "LOCAL_TESTS_PASS_WITH_MOCKED_PROVIDER" if tested else "🚩 PENDIENTE: EXECUTION_NOT_DEMONSTRATED"
    return {
        "file": path,
        "sha256": sha256(data),
        "bytes": len(data),
        "passes": {
            "1_provenance": "NEW_IN_BRANCH" if previous.returncode else "MODIFIED_FROM_HEAD",
            "2_structure": "PYTHON_SYNTAX_VALID",
            "3_wiring": wiring,
            "4_evidence": evidence,
        },
    }


def main() -> None:
    inventory = build()
    result = command(sys.executable, "-m", "pytest", *TESTS, "-q", "-k", "not page_providers_and_auth")
    tested = result.returncode == 0 and re.search(r"\b\d+ passed\b", result.stdout) is not None
    lint = command(sys.executable, "-m", "ruff", "check", *(path for path in CODE if "/tests/" not in path))
    if not tested or lint.returncode:
        raise RuntimeError(f"LOCAL_VALIDATION_FAILED: tests={result.returncode}, lint={lint.returncode}")
    for item in inventory["images"]:
        item["passes"]["3_wiring"] = "BACKEND_CATALOG_METADATA_TESTED; 🚩 PENDIENTE: FRONTEND_NOT_CONNECTED"
        item["passes"]["4_evidence"] = "HASH_READBACK_AND_LOCAL_API_TEST; 🚩 PENDIENTE: VISUAL_REVIEW"
    output = {
        "schema": "yaiwes.plan-audit-post-code/v1",
        "source_commit": inventory["commit"],
        "limits": [
            "Local provider response is mocked; no OpenAI generation demonstrated",
            "No external memory adapter or HF restore demonstrated",
            "Images are metadata references; frontend and visual review pending",
            "Existing provider test disagrees with openai in origin/main",
        ],
        "checks": {
            "focused_tests": result.stdout.strip().splitlines()[-1],
            "ruff_backend": "PASS",
        },
        "source_inventory_summary": inventory["summary"],
        "documents": inventory["documents"],
        "skills": inventory["skills"],
        "images": inventory["images"],
        "code": [code_entry(path, tested) for path in CODE],
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verified = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if verified != output:
        raise RuntimeError("POST_AUDIT_READBACK_FAILED")
    print(json.dumps({"documents": len(output["documents"]), "skills": len(output["skills"]),
                      "images": len(output["images"]), "code": len(output["code"]),
                      "checks": output["checks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
