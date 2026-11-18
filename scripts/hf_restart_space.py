#!/usr/bin/env python3
"""hf_restart_space.py — Sonda de estado y reinicio de los Spaces del router.

QUE HACE (3 pasos, en este orden)
  1. GET  https://huggingface.co/api/spaces/{ns}/{repo}      -> estado real (sdk/stage)
  2. POST https://huggingface.co/api/spaces/{ns}/{repo}/restart  -> reinicio
     SOLO si se pasa --apply. Sin --apply es DRY-RUN: no escribe nada.
  3. GET  https://comand-center-1-{space}.hf.space/health    -> comprueba que levanta

ALCANCE Y SEGURIDAD
  · Solo reinicia. NO crea, NO borra y NO modifica secrets ni ficheros.
  · El inventario de Spaces NO se re-inventa aqui: se toma de
    external/core/space_inventory.py (fuente unica, 6 Spaces en 2 grupos).
  · El token se lee de HF_TOKEN (o HF_TOKEN_1_NEW) y NUNCA se imprime.
  · Sin PRO ni creditos prepago HF responde 402 en el reinicio: el script lo
    distingue y lo reporta como tal (no lo disfraza de otro error).

USO
  python3 scripts/hf_restart_space.py --list
  python3 scripts/hf_restart_space.py --space local-llm-router
  python3 scripts/hf_restart_space.py --space local-llm-router --apply
  python3 scripts/hf_restart_space.py --all --apply

CODIGOS DE SALIDA
  0  todo correcto (Space running y /health responde 200)
  1  error de uso o error de API inesperado
  2  el Space existe pero esta parado (paused/stopped) y no se reinicio
  3  HF respondio 402 (falta PRO o creditos) -> el reinicio no se puede hacer
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from external.core.space_inventory import (  # noqa: E402
    NAMESPACE,
    RETIRED_SPACES,
    all_spaces,
    group_of,
    hf_repo_id,
    space_url,
)

API = "https://huggingface.co/api/spaces"
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_PAUSED = 2
EXIT_NO_CREDIT = 3


def _token() -> str:
    return os.getenv("HF_TOKEN") or os.getenv("HF_TOKEN_1_NEW") or ""


def _request(method: str, url: str, token: str, timeout: int = 20):
    """Devuelve (status, body_texto). Status 0 = sin red."""
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def space_state(space: str, token: str) -> dict:
    """Estado real del Space segun la API de HF."""
    repo = hf_repo_id(space)
    status, body = _request("GET", f"{API}/{repo}", token)
    out = {"space": space, "repo": repo, "group": group_of(space), "http": status}
    if status == 200:
        try:
            data = json.loads(body)
            runtime = data.get("runtime") or {}
            out["sdk"] = data.get("sdk")
            out["stage"] = runtime.get("stage") or data.get("stage")
            out["paused"] = out["stage"] in ("PAUSED", "STOPPED", "SLEEPING")
        except Exception as e:
            out["error"] = f"json invalido: {e}"
    elif status == 404:
        out["error"] = "no existe en HF (404)"
    else:
        out["error"] = body[:200]
    return out


def health(space: str, timeout: int = 20) -> dict:
    """Comprueba /health del Space (200 = vivo)."""
    url = space_url(space, "health")
    status, body = _request("GET", url, "", timeout=timeout)
    return {"url": url, "http": status, "body": body[:160] if status != 200 else ""}


def restart(space: str, token: str) -> dict:
    """POST de reinicio. Solo lo llama el modo --apply."""
    repo = hf_repo_id(space)
    status, body = _request("POST", f"{API}/{repo}/restart", token)
    out = {"http": status}
    if status == 200:
        out["result"] = "reinicio solicitado"
    elif status == 402:
        out["result"] = "HF exige PRO o creditos prepago (402): no se puede reiniciar"
    elif status == 404:
        out["result"] = "el Space no existe (404)"
    else:
        out["result"] = body[:200]
    return out


def report(space: str, apply: bool, token: str) -> dict:
    out = {"space": space, "state": space_state(space, token)}
    if apply:
        out["restart"] = restart(space, token)
    else:
        out["restart"] = {"skipped": "dry-run: pase --apply para reiniciar de verdad"}
    out["health"] = health(space)
    return out


def _verdict(rep: dict) -> int:
    if rep["state"].get("http") == 404:
        return EXIT_ERROR
    if rep["state"].get("http") not in (200,):
        return EXIT_ERROR
    if rep.get("restart", {}).get("http") == 402:
        return EXIT_NO_CREDIT
    if rep["state"].get("paused") and not rep.get("restart", {}).get("http") == 200:
        return EXIT_PAUSED
    if rep["health"].get("http") == 200:
        return EXIT_OK
    return EXIT_PAUSED


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sonda de estado/reinicio de los Spaces del router")
    ap.add_argument("--space", action="append", default=[], help="nombre corto del Space (repetible)")
    ap.add_argument("--all", action="store_true", help="todos los Spaces del inventario")
    ap.add_argument("--list", action="store_true", help="solo listar el inventario")
    ap.add_argument("--apply", action="store_true", help="reiniciar de verdad (sin esto: dry-run)")
    args = ap.parse_args(argv)

    if args.list:
        for s in all_spaces():
            print(f"{s:24} group={group_of(s):8} repo={hf_repo_id(s)}")
        for s in RETIRED_SPACES:
            print(f"{s:24} RETIRADO (no existe en HF)")
        return EXIT_OK

    spaces = list(args.space)
    if args.all:
        spaces = all_spaces()
    if not spaces:
        ap.error("indica --space <nombre>, --all o --list")

    token = _token()
    if args.apply and not token:
        print("FALLO: --apply necesita HF_TOKEN en el entorno", file=sys.stderr)
        return EXIT_ERROR

    worst = EXIT_OK
    for s in spaces:
        if s not in all_spaces():
            print(f"{s:24} ERROR: no esta en el inventario canonico", file=sys.stderr)
            worst = EXIT_ERROR
            continue
        rep = report(s, args.apply, token)
        st = rep["state"]
        print(f"{s:24} api={st.get('http')} stage={st.get('stage')} paused={st.get('paused')} "
              f"health={rep['health'].get('http')} restart={rep.get('restart', {}).get('result', rep.get('restart', {}).get('skipped'))}")
        if st.get("http") != 200:
            print(f"    detalle: {st.get('error', '')}", file=sys.stderr)
        worst = max(worst, _verdict(rep))
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
