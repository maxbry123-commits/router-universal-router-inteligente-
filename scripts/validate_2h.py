#!/usr/bin/env python3
"""validate_2h.py — MINIMAX 2H · validador fail-closed del motor determinista + artefactos.

Comprueba, con ejecucion REAL (no mocks):

  1. El modulo chat_engine importa y distingue peticion de ARCHIVO de peticion normal.
  2. La respuesta determinista se apoya en el estado REAL (los 6 agentes del
     registro central con su interruptor real).
  3. El artefacto se ESCRIBE de verdad en disco y el sha256 devuelto coincide
     con el sha256 del fichero leido (prueba con hashlib, no con la respuesta).
  4. La cadena del chat NO devuelve 503 cuando no hay proveedor externo: el
     proxy responde 200 con provider="determinista" (prueba funcional).
  5. El bloque del artefacto cabe en las 5 primeras lineas que conserva el
     render F3 -> el chat MUESTRA el archivo (render real de nct_format).
  6. El campo JSON "artifacts" viene poblado (nombre, sha256, bytes).
  7. NINGUN fichero de frontend tocado: git diff de chat-router/** vacio.
  8. El parche es idempotente: re-ejecutarlo no cambia nada.

Salida: una linea por check. RC 0 solo si TODOS pasan.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

RESULTS = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} · {name}" + (f" · {detail}" if detail else ""))
    return bool(ok)


def main() -> int:
    # ── V1 · el modulo y la deteccion de peticion de archivo ────────────────
    try:
        from router_llm_hf import chat_engine
        import_ok = True
    except Exception as e:
        chat_engine = None
        import_ok = False
        check("V1 el modulo chat_engine importa", False, f"{type(e).__name__}: {e}")
    if import_ok:
        p1 = chat_engine.pide_archivo("crea un informe en markdown con el estado real del router")
        p2 = chat_engine.pide_archivo("hola, como estas?")
        check("V1 el modulo chat_engine importa y detecta la peticion de archivo",
              bool(p1) and p1.get("kind") == "md" and p2 is None,
              f"archivo={p1} normal={p2}")

    # ── V2 · estado REAL ────────────────────────────────────────────────────
    est = chat_engine.estado_real()
    agentes = est.get("agentes") or []
    nombres = sorted(a["nombre"] for a in agentes)
    con_interruptor = all("on" in a for a in agentes)
    check("V2 el motor determinista se apoya en el estado REAL (6 agentes con interruptor)",
          len(agentes) == 6 and con_interruptor,
          f"agentes={nombres} interruptores={'ok' if con_interruptor else 'mal'}")

    # ── V3 · el archivo se escribe de verdad y el sha256 es real ────────────
    with tempfile.TemporaryDirectory(prefix="artefactos-2h-") as tmp:
        det = chat_engine.responde(
            "crea un informe en markdown con el estado real del router",
            artifact_dir=tmp, artifact_kinds=("md", "txt"))
        arts = det.get("artifacts") or []
        if not arts:
            check("V3 el artefacto se escribe de verdad en disco", False, "no se devolvio ningun artefacto")
        else:
            a = arts[0]
            ruta = Path(a["path"])
            existe = ruta.is_file()
            real = hashlib.sha256(ruta.read_bytes()).hexdigest() if existe else ""
            tam = ruta.stat().st_size if existe else 0
            check("V3 el artefacto se escribe de verdad en disco (sha256 del fichero)",
                  existe and real == a["sha256"] and tam == a["bytes"] and real != "",
                  f"fichero={ruta.name} sha_devuelto={a['sha256'][:16]} sha_real={real[:16]} bytes={tam}")

            # ── V5 · el chat LO MUESTRA: el render F3 se queda con 5 lineas ──
            from router_llm_hf import nct_format as nct
            f3 = nct.render_f3({"objetivo": "prueba", "texto": det["content"],
                                "estado": "EXECUTING", "motores_activos": True})
            lineas = [l for l in det["content"].splitlines() if l.strip()][:5]
            caben = all(l in f3 for l in lineas)
            check("V5 el bloque del artefacto cabe en el render F3 (el chat lo muestra)",
                  caben and "ARTEFACTO CREADO" in f3 and a["sha256"][:16] in f3,
                  f"lineas_visibles={len(lineas)} artefacto_en_f3={'ARTEFACTO CREADO' in f3}")

    # ── V4 · el proxy responde 200 (NO 503) sin proveedor externo ──────────
    sys.path.insert(0, str(REPO / "ROUTER MVP v1" / "system_prompt_py"))
    os.environ["ROUTER_API_KEY"] = "dummy-2h"
    os.environ.setdefault("ARTIFACT_DIR", tempfile.mkdtemp(prefix="artefactos-proxy-2h-"))
    spec = importlib.util.spec_from_file_location(
        "proxy_2h", REPO / "ROUTER MVP v1" / "system_prompt_py" / "openai_compatible_proxy.py")
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    try:
        from fastapi.testclient import TestClient
        with TestClient(proxy.app) as client:
            r = client.post("/v1/chat/completions", headers={"x-api-key": "dummy-2h"},
                             json={"model": "minimaxai/minimax-m3.1-flash",
                                   "messages": [{"role": "user",
                                                 "content": "crea un informe en markdown del router"}]})
            codigo = r.status_code
            cuerpo = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    except Exception as e:
        codigo, cuerpo = 0, {"error": f"{type(e).__name__}: {e}"}
    contenido = ((cuerpo.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    check("V4 la cadena del chat NO da 503 sin proveedor externo (responde el motor determinista)",
          codigo == 200 and cuerpo.get("provider") == "determinista" and "ARTEFACTO CREADO" in contenido,
          f"http={codigo} provider={cuerpo.get('provider')} contenido={'ARTEFACTO CREADO' in contenido}")

    # ── V6 · el campo JSON artifacts viene poblado ─────────────────────────
    arts_json = cuerpo.get("artifacts") or []
    check("V6 la respuesta JSON trae el campo artifacts poblado (nombre, sha256, bytes)",
          bool(arts_json) and arts_json[0].get("sha256") and arts_json[0].get("bytes") is not None,
          f"artifacts={[(a.get('name'), (a.get('sha256') or '')[:12]) for a in arts_json]}")

    # ── V7 · NINGUN fichero de frontend tocado ──────────────────────────────
    try:
        diff = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", "HEAD", "--",
                               "chat-router"], capture_output=True, text=True).stdout.strip()
        staged = subprocess.run(["git", "-C", str(REPO), "diff", "--cached", "--name-only", "--",
                                 "chat-router"], capture_output=True, text=True).stdout.strip()
        check("V7 NINGUN fichero de frontend tocado (chat-router/** intacto)",
              not diff and not staged,
              f"modificados={diff or 0} staged={staged or 0}")
    except Exception as e:
        check("V7 NINGUN fichero de frontend tocado (chat-router/** intacto)", False, str(e))

    # ── V8 · el parche es idempotente ──────────────────────────────────────
    try:
        out = subprocess.run([sys.executable, str(REPO / "scripts" / "patch_2h_chat_engine.py")],
                             capture_output=True, text=True, cwd=str(REPO))
        check("V8 el parche del proxy es idempotente (re-ejecutarlo no cambia nada)",
              out.returncode == 0 and "TOTAL: 0 cambio(s)" in out.stdout,
              out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[:120])
    except Exception as e:
        check("V8 el parche del proxy es idempotente (re-ejecutarlo no cambia nada)", False, str(e))

    # ── RESUMEN ────────────────────────────────────────────────────────────
    fallos = [n for n, ok, _ in RESULTS if not ok]
    print(f"\nRESUMEN 2H: {len(RESULTS) - len(fallos)}/{len(RESULTS)} PASS")
    if fallos:
        for n in fallos:
            print(f"  FAIL: {n}")
        return 1
    print("VALIDACION 2H: TODO PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
