#!/usr/bin/env python3
"""patch_2h_chat_engine.py — MINIMAX 2H · motor determinista + artefactos en el chat.

SOLO BACKEND: toca un unico fichero, el proxy
"ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py". NO toca el frontend
(chat-router/**) ni ninguna ventana del chat: el chat ya pinta lo que el backend
devuelve en choices[0].message.content, asi que el archivo se ve SIN tocar nada
de la interfaz.

Cambios (reemplazo literal, fail-closed si el texto no aparece):

  1. Nuevo helper _motor_determinista(messages, respuesta_externa="") que
     llama a router_llm_hf.chat_engine.responde(): responde con el estado REAL
     del sistema y, si el mensaje pide un archivo, lo ESCRIBE en el store de
     artefactos (sha256 real) y devuelve el bloque del artefacto.

  2. La rama "provider == none" (hoy: 503 y el chat muerto cuando no hay clave
     de NVIDIA/Groq y los Spaces estan PAUSED por 402) pasa a responder con el
     motor determinista. El diagnostico se conserva.

  3. En la respuesta normal (proveedor real), si el mensaje pide archivo, se
     adjunta el bloque del artefacto al contenido y se anade el campo
     "artifacts" (JSON) para consumidores programaticos.

Idempotente: si el parche ya esta aplicado, no escribe nada.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROXY = REPO / "ROUTER MVP v1" / "system_prompt_py" / "openai_compatible_proxy.py"

# ── 1. helper antes de _run_chat_chain ─────────────────────────────────────
ANCLA_1 = '''async def _run_chat_chain(messages, model_requested, *, service_mode=None, route_path="",
                          detected_mode=None, adapter=None, agent=None):'''
HELPER = '''def _motor_determinista(messages, respuesta_externa: str = "") -> dict:
    """Ultimo eslabon de la cadena del chat + materializacion del archivo.

    Si Local (Space GGUF), NVIDIA y Groq fallan, la cadena se queda sin
    proveedor. Antes el proxy devolvia 503 y el chat quedaba muerto. Ahora
    responde el motor determinista local, con el estado REAL del sistema; y si
    el mensaje pide un archivo, lo escribe de verdad en el store de artefactos
    (sha256 real) y devuelve el bloque para que el chat lo muestre.
    """
    prompt = ""
    for _m in messages or []:
        if _m.get("role") == "user":
            prompt = _m.get("content") or ""
            break
    try:
        from router_llm_hf import chat_engine
        det = chat_engine.responde(
            prompt,
            artifact_dir=ARTIFACT_DIR,
            artifact_kinds=ARTIFACT_KINDS,
            respuesta_externa=respuesta_externa,
        )
    except Exception as e:  # pragma: no cover - el error se ve, no se esconde
        print(f"[DETERMINISTA] no disponible: {type(e).__name__}: {e}")
        det = {"content": f"Motor determinista no disponible: {e}", "artifacts": [],
               "tipo": "error", "modo": "determinista"}
    if respuesta_externa:
        det["content"] = f"{respuesta_externa}\\n\\n{det.get('content') or ''}"
    return det


''' + ANCLA_1

# ── 2. rama "provider == none" ──────────────────────────────────────────────
VIEJO_2 = '''        if fallback_result.get("provider") == "none":
            # 503 con diagnostico real (conteo de claves y ultimo error), no una cadena generica
            return JSONResponse(status_code=503, content={
                "detail": "Todos los proveedores fallaron",
                "diag": fallback_result.get("diag") or {},
                "mode": detected_mode,
                "service_mode": service_mode,
                "route": route_path,
            })'''
NUEVO_2 = '''        if fallback_result.get("provider") == "none":
            # MINIMAX 2H: la cadena se queda sin proveedor externo (NVIDIA/Groq
            # sin clave, Spaces PAUSED por 402). Antes: 503 y el chat muerto.
            # Ahora el ultimo eslabon es el motor determinista local, que
            # responde con el estado REAL del sistema. El diagnostico se
            # conserva: el error nunca se pierde en silencio.
            det = _motor_determinista(messages)
            return JSONResponse({
                "id": "chatcmpl-determinista",
                "object": "chat.completion",
                "provider": "determinista",
                "degraded": True,
                "mode": detected_mode,
                "service_mode": service_mode,
                "route": route_path,
                "agent": agent,
                "model": model_requested,
                "diag": fallback_result.get("diag") or {},
                "artifacts": det.get("artifacts") or [],
                "tipo": det.get("tipo"),
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": det.get("content") or ""},
                    "finish_reason": "stop"
                }]
            })'''

# ── 3. artefacto en la respuesta normal ────────────────────────────────────
VIEJO_3 = '''        # 4. Respuesta con el contenido real del proveedor.
        return JSONResponse({
            "id": "chatcmpl-fallback",
            "object": "chat.completion",
            "provider": provider_used,
            "agent": agent,
            "degraded": bool(fallback_result.get("degraded")),'''
NUEVO_3 = '''        # 4. Si el mensaje pide un archivo, se materializa (sha256 real) y el
        #    bloque del artefacto se antepone al contenido: el chat lo muestra.
        _prompt = ""
        for _m in messages or []:
            if _m.get("role") == "user":
                _prompt = _m.get("content") or ""
                break
        artifacts: list = []
        try:
            from router_llm_hf.chat_engine import pide_archivo
            _pide = pide_archivo(_prompt)
        except Exception:
            _pide = None
        if _pide:
            det = _motor_determinista(messages, respuesta_externa=content)
            artifacts = det.get("artifacts") or []
            content = det.get("content") or content

        # 5. Respuesta con el contenido real del proveedor.
        return JSONResponse({
            "id": "chatcmpl-fallback",
            "object": "chat.completion",
            "provider": provider_used,
            "agent": agent,
            "artifacts": artifacts,
            "degraded": bool(fallback_result.get("degraded")),'''


def _reemplaza(src: str, viejo: str, nuevo: str, etiqueta: str, ya_aplicado=None) -> tuple:
    # MINIMAX 2G/C7: el helper del motor determinista puede estar en su forma
    # original (2H) o en la forma consolidada por C7 (delegada a
    # external/core/provider_fallback.deterministic_fallback). Ambas valen.
    if ya_aplicado:
        marcas = ya_aplicado if isinstance(ya_aplicado, (tuple, list)) else (ya_aplicado,)
        if any(m in src for m in marcas):
            return src, 0, f"{etiqueta}: ya aplicado"
        return src, 0, f"{etiqueta}: ya aplicado"
    if nuevo in src:
        return src, 0, f"{etiqueta}: ya aplicado"
    if viejo not in src:
        raise SystemExit(f"FALLO: {etiqueta}: no se encuentra el texto exacto (fail-closed)")
    return src.replace(viejo, nuevo, 1), 1, f"{etiqueta}: aplicado"


def main() -> int:
    if not PROXY.exists():
        raise SystemExit(f"FALLO: no existe {PROXY}")
    src = PROXY.read_text(encoding="utf-8")
    cambios = 0
    for viejo, nuevo, etiqueta, ya in (
            (ANCLA_1, HELPER, "helper _motor_determinista", "def _motor_determinista("),
            (VIEJO_2, NUEVO_2, "rama provider=none", None),
            (VIEJO_3, NUEVO_3, "artefacto en respuesta",
             ('"artifacts": _validate_artifacts(artifacts),', '"artifacts": artifacts,'))):
        src, n, msg = _reemplaza(src, viejo, nuevo, etiqueta, ya)
        cambios += n
        print(f"{'OK   ' if n else 'SIN  '} {msg}")
    if cambios:
        PROXY.write_text(src, encoding="utf-8")
    print(f"TOTAL: {cambios} cambio(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
