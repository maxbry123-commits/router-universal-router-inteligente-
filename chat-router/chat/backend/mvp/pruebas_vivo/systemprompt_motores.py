"""Smoke test en el Space EXISTENTE, sin Jobs ni infraestructura nueva.

Desde el checkout de Hugging Face (router-mvp/):
  RIU_KEY="$RIU_API_KEY" python -m mvp.pruebas_vivo.systemprompt_motores --base http://127.0.0.1:7860 --inferir

Sin --inferir: prueba el prompt y el motor de lectura sin consumir tokens.
No imprime claves, no altera prompt_on y no escribe código en GitHub.
La cola de prueba solo LISTA su propia carpeta de recibos (_cola).
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

URL_DEFECTO = "https://comand-center-1-riu-router.hf.space"
REPO = Path(__file__).resolve().parents[5]
REPORTES = []


def fila(nombre, correcto, evidencia):
    estado = "PASS" if correcto else "GAP"
    ev = str(evidencia).replace(os.environ.get("RIU_KEY") or "\0", "[OCULTO]")[:180]
    REPORTES.append((nombre, estado, ev))
    print(f"{estado} {nombre}: {ev}", flush=True)


def pedir(base, key, ruta, contenido=None, timeout=25):
    cab = {"X-API-Key": key, "Accept": "application/json"}
    if contenido is not None:
        cab["Content-Type"] = "application/json"
    req = urllib.request.Request(
        base.rstrip("/") + ruta,
        data=None if contenido is None else json.dumps(contenido).encode("utf-8"),
        headers=cab, method="GET" if contenido is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read(3_000_000))
    except urllib.error.HTTPError as e:
        try:
            doc = json.loads(e.read(2000))
        except (ValueError, UnicodeError):
            doc = {}
        return e.code, doc


def seguro(base, key, ruta, contenido=None, timeout=25):
    try:
        return pedir(base, key, ruta, contenido, timeout)
    except (OSError, ValueError, TimeoutError) as e:
        return 0, {"error": type(e).__name__}


def analizar(base, clave, modelos):
    status, h = seguro(base, clave, "/health")
    cab = h.get("commit", "") if isinstance(h, dict) else ""
    repo_head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                               text=True, capture_output=True, timeout=12)
    head = repo_head.stdout.strip() if repo_head.returncode == 0 else ""
    fila("Space health HTTP y commit ejecutado", status == 200 and h.get("status") == "ok"
         and bool(cab) and bool(head) and head.startswith(cab[:7]),
         f"HTTP {status}; ejecutando={str(cab)[:10]}; checkout={head[:10]}")

    pstatus, ctrl = seguro(base, clave, "/plugins/puente_chat/call/agent_access_lock", {})
    data = ctrl.get("result") or {}
    locked = data.get("prompt_locked")
    fila("Router control de System Prompt (solo lectura)",
         pstatus == 200 and ctrl.get("status") == "ok" and type(locked) is bool,
         f"HTTP {pstatus}; prompt_locked={locked!r}")

    bstatus, bridge = seguro(base, clave, "/web/v1/system-prompt-on")
    esperado = None if type(locked) is not bool else not locked
    fila("Bridge SWE CODE usa el mismo ON/OFF del Router",
         bstatus == 200 and bridge.get("ok") is True and
         type(bridge.get("on")) is bool and bridge["on"] == esperado,
         f"HTTP {bstatus}; Router={esperado!r}; bridge={bridge.get('on')!r}")

    capstatus, cap = seguro(base, clave, "/chat/swe/capacidades")
    agentes = cap.get("agentes") if isinstance(cap.get("agentes"), dict) else {}
    for a in ("codex", "opencode", "openhands", "swe-agent", "claude-code", "openclaw"):
        d = agentes.get(a) or {}
        fila(f"Agente registrado y listo: {a}",
             capstatus == 200 and d.get("disponible") is True,
             f"{d.get('estado','SIN_VERIFICAR')}; causa={d.get('causa','sin dato')}")

    rstatus, raiz = seguro(base, clave, "/plugins/motor_archivos/call/raiz", {})
    rr = raiz.get("result") or {}
    fila("Motor archivos responde al Router HTTP", rstatus == 200 and
         raiz.get("status") == "ok" and rr.get("libre_bytes", -1) >= 0 and
         bool(rr.get("raiz")), f"HTTP {rstatus}; disponible={bool(rr.get('raiz'))}")

    # Ejecucion del motor real: 1 operacion de lectura. No copia ni modifica
    # archivos del usuario; solo crea el recibo normal de esta cola de pruebas.
    if rstatus == 200 and bool(rr.get("raiz")):
        qstatus, lanzada = seguro(
            base, clave, "/plugins/motor_archivos/call/ejecutar",
            {"cola": [{"accion": "listar", "origen": "_cola", "max": 1}]})
        qid = (lanzada.get("result") or {}).get("id") or ""
        final = None
        for _ in range(16):
            if not qid:
                break
            time.sleep(0.5)
            _, respuesta = seguro(base, clave, "/plugins/motor_archivos/call/estado", {"id": qid})
            final = respuesta.get("result") or {}
            if final.get("estado") in ("terminado", "error", "cancelado"):
                break
        trabajos = final.get("trabajos", []) if isinstance(final, dict) else []
        ok = bool(qid) and final.get("estado") == "terminado" and len(trabajos) == 1 and trabajos[0].get("estado") == "ok"
        fila("Motor real ejecuta LISTAR y entrega recibo", ok,
             f"HTTP {qstatus}; cola={qid[:12]}; estado={(final or {}).get('estado','sin respuesta')}")
    else:
        fila("Motor real ejecuta LISTAR y entrega recibo", False, "motor raiz no disponible")

    from mvp import prompt
    sys_texto = prompt.sistema()
    fila("Core y bloques 3/4 originales legibles",
         "[CREACIÓN DE CÓDIGO]" in sys_texto and
         "BLOQUE 4/5" in sys_texto and len(sys_texto) > 1000,
         f"longitud={len(sys_texto)}; fuente=router-mvp/fichas/system-prompt")

    from plugins.deepseek_harness import server as harness
    orig = [{"role": "user", "content": "PING_SYSTEMPROMPT"}]
    for on in (True, False):
        with patch.object(harness, "_router", return_value={"prompt_locked": not on}):
            mensajes = harness._mensajes_swe_con_prompt(orig)
            with patch.object(harness, "ejecutar_agente", return_value={"ok": True}) as mock:
                harness._ejecutar_agente_con_prompt(
                    "codex", "test-only", "hf/qwen3-0.6b", "PING", "",
                    {}, {})
                ctx = mock.call_args.args[4]
        correcto = (len(mensajes) == (2 if on else 1) and
                    (mensajes[0].get("role") == "system") == on and
                    (("[CREACIÓN DE CÓDIGO]" in ctx) == on))
        fila(f"Harness inyecta prompt en LLM/agente ON={on}", correcto,
             f"roles={[m['role'] for m in mensajes]}; agente_mock_invocado={mock.called}")

    # Suite JS del mismo deploy: verifica identidad byte a byte del Core
    # Python/JS y bloqueos. Node existe en el Dockerfile del Space.
    caso = REPO / "chat-router" / "SWE CODE" / "web-bridge" / "test" / "systemprompt_router.test.mjs"
    try:
        t = subprocess.run(["node", "--test", str(caso)], cwd=str(REPO),
                           capture_output=True, text=True, timeout=100)
        fila("Tests Node: ficha completa e identidad Python/JS",
             t.returncode == 0, f"exit={t.returncode}; " +
             (t.stdout[-150:] if t.returncode == 0 else t.stderr[-150:]))
    except (OSError, subprocess.TimeoutExpired) as e:
        fila("Tests Node: ficha completa e identidad Python/JS", False, type(e).__name__)

    for modelo in modelos:
        c, doc = seguro(
            base, clave, "/plugins/deepseek_harness/modelos/v1/chat/completions",
            {"model": modelo, "messages": [
                {"role": "user", "content": "Responde exactamente: PONG-SYSTEMPROMPT"}],
             "tools": False, "stream": False, "max_tokens": 45}, timeout=90)
        choices = doc.get("choices") or []
        mensaje = choices[0].get("message") or {} if choices else {}
        fin = choices[0].get("finish_reason") if choices else None
        texto = mensaje.get("content") or ""
        fila(f"Inferencia REAL por Harness modelo={modelo}",
             c == 200 and bool(texto.strip()) and fin in ("stop", "end_turn", "eos"),
             f"HTTP {c}; modelo={str(doc.get('modelo_usado') or doc.get('model') or '')[:60]}; "
             f"finish_reason={fin!r}; respuesta={str(texto)[:60]!r}")


def main():
    p = argparse.ArgumentParser(description="Prueba HF real de System Prompt y motores sin Jobs")
    p.add_argument("--base", default=URL_DEFECTO)
    p.add_argument("--inferir", action="store_true",
                   help="hacer una llamada real a un modelo local, con consumo de tokens")
    p.add_argument("--modelo", action="append", default=[],
                   help="modelo real por id; repetir para varios")
    args = p.parse_args()
    key = os.environ.get("RIU_KEY") or os.environ.get("RIU_API_KEY")
    if not key:
        p.error("requiere RIU_KEY o RIU_API_KEY en el entorno; nunca en la URL")
    analizar(args.base.rstrip("/"), key,
             (args.modelo or ["lfm2.5-350m"]) if args.inferir else [])
    n = sum(r[1] == "PASS" for r in REPORTES)
    print(f"RESULTADO {n}/{len(REPORTES)} PASS; GAP={len(REPORTES)-n}", flush=True)
    return 0 if n == len(REPORTES) else 1


if __name__ == "__main__":
    sys.exit(main())
