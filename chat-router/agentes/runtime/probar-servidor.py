#!/usr/bin/env python3
"""Diagnostico HTTPS SOLO LECTURA del Space SWE CODE; no expone claves ni crea tareas.
Uso: RIU_API_KEY=(secreto del entorno) python agentes/runtime/probar-servidor.py --commit <sha>
El codigo se instala en la misma raiz existente y puede ejecutarse en un job de pruebas.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

AGENTES = frozenset(("openclaw", "swe-agent", "openhands", "opencode", "codex", "claude-code"))
PUBLICO = "https://comand-center-1-riu-router.hf.space"
LOOPBACK = "http://127.0.0.1:7860"


class SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


ABRIDOR = urllib.request.build_opener(SinRedireccion)


def pedir(base, path, clave="", post=None):
    data = None if post is None else json.dumps(post).encode("utf-8")
    headers = {"accept": "application/json"}
    if clave:
        headers["x-api-key"] = clave
        headers["authorization"] = "Bearer " + clave
    if data is not None:
        headers["content-type"] = "application/json"
    try:
        req = urllib.request.Request(base + path, headers=headers, data=data)
        with ABRIDOR.open(req, timeout=12) as respuesta:
            texto = respuesta.read(2_000_000)
            return respuesta.status, json.loads(texto)
    except urllib.error.HTTPError as err:
        return err.code, None
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return 0, None


def obtener_agentes(doc):
    if not isinstance(doc, dict):
        return {}
    lista = doc.get("agents")
    if isinstance(lista, list):
        return {a["id"]: a for a in lista if isinstance(a, dict) and isinstance(a.get("id"), str)}
    lista = doc.get("agentes")
    return lista if isinstance(lista, dict) else {}


def comprobar(base, clave, commit):
    checks = {}
    http, health = pedir(base, "/health")
    hash_real = str((health or {}).get("commit") or "")
    auto = (health or {}).get("autoactualizacion") or {}
    checks["health"] = {"http": http, "ok": http == 200 and isinstance(health, dict),
                        "commit": hash_real[:10] if re.fullmatch("[0-9a-fA-F]{7,40}", hash_real) else None,
                        "autopull": auto.get("estado") if isinstance(auto, dict) else None}
    if commit:
        checks["commit"] = {"ok": hash_real.lower().startswith(commit.lower()), "esperado": commit[:10]}
    if not clave:
        checks["autenticacion"] = {"ok": False, "motivo": "FALTA_RIU_API_KEY_EN_ENTORNO"}
        return checks

    for nombre, ruta in (("yaiwes", "/chat/agents"),
                         ("capacidades_yaiwes", "/chat/swe/capacidades"),
                         ("capacidades_openclaw", "/web/v1/swe/capacidades")):
        status, doc = pedir(base, ruta, clave)
        agentes = obtener_agentes(doc)
        if nombre != "yaiwes":
            agentes = obtener_agentes(doc) if isinstance(doc, dict) else {}
        validos = set(agentes) == AGENTES
        operativos = sorted(k for k, v in agentes.items()
                           if k in AGENTES and isinstance(v, dict) and v.get("disponible") is True)
        checks[nombre] = {"http": status, "ok": status == 200 and validos and len(operativos) == len(AGENTES),
                          "catalogo_ok": validos, "operativos": operativos,
                          "no_operativos": sorted(AGENTES - set(operativos)),
                          "registrados": sorted(set(agentes) & AGENTES),
                          "faltantes": sorted(AGENTES - set(agentes))}
        if isinstance(doc, dict) and "harness" in doc:
            checks[nombre]["harness"] = str(doc["harness"])[:28]
        if validos:
            checks[nombre]["estados"] = {k: str((v or {}).get("estado") or "SIN VERIFICAR")[:45]
                                            for k, v in agentes.items() if isinstance(v, dict)}

    status, doc = pedir(base, "/plugins/deepseek_harness/invoke", clave, post={"action": "status"})
    result = (doc or {}).get("result") or {}
    swe = result.get("swe") or {}
    agentes = obtener_agentes(swe)
    operativos = sorted(k for k, v in agentes.items()
                       if k in AGENTES and isinstance(v, dict) and v.get("disponible") is True)
    checks["harness"] = {"http": status, "ok": status == 200 and set(agentes) == AGENTES
                         and len(operativos) == len(AGENTES), "operativos": operativos,
                         "no_operativos": sorted(AGENTES - set(operativos)),
                         "faltantes": sorted(AGENTES - set(agentes))}
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", choices=(PUBLICO, LOOPBACK), default=PUBLICO)
    parser.add_argument("--commit", default="", help="SHA esperado de GitHub main")
    args = parser.parse_args()
    if args.commit and not re.fullmatch("[0-9a-fA-F]{7,40}", args.commit):
        parser.error("--commit requiere SHA hexadecimal")
    clave = os.environ.get("RIU_API_KEY", "").strip()
    checks = comprobar(args.url, clave, args.commit)
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    return 0 if checks and all(v.get("ok", False) for v in checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())