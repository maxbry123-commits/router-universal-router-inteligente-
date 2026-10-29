"""router_api: puerta HTTP delgada del edificio 1 para el edificio 2 (plugins).

Envuelve funciones EXISTENTES de integration.chat_mvp (memoria_loader, providers, vault_hook) sin duplicar logica.
Los plugins llaman por POST /plugins/router_api/call/<accion>; nunca importan integration.chat_mvp.
"""
from __future__ import annotations

import time
from typing import Any

_MEM_OPS = {"save", "load", "search", "sqlite_save", "sqlite_load", "sqlite_health"}


def _mem_op(payload: dict[str, Any]) -> dict[str, Any]:
    op = str(payload.get("op") or "")
    if op not in _MEM_OPS:
        return {"status": "degraded", "reason": "op de memoria no permitida"}
    from integration.chat_mvp.memoria_loader import _memory

    m = _memory()
    fn = {"save": m.save, "load": m.load, "search": m.search, "sqlite_save": m.sqlite.save, "sqlite_load": m.sqlite.load, "sqlite_health": m.sqlite.health}[op]
    return {"status": "ok", "valor": fn(*list(payload.get("args") or []), **dict(payload.get("kwargs") or {}))}


def _chat(payload: dict[str, Any]) -> dict[str, Any]:
    # mismo bucle que tenia puente_chat._api: varias claves, mismo modelo, con plazo total `tope`
    from integration.chat_mvp import providers

    proveedor, modelo = str(payload.get("proveedor") or ""), str(payload.get("modelo") or "")
    mensajes, max_tokens, tope = payload.get("mensajes") or [], int(payload.get("max_tokens") or 1024), int(payload.get("tope") or 60)
    claves = providers.env_keys(proveedor)
    if not claves:
        return {"error": "SIN_CLAVES_" + proveedor.upper()}
    fin = time.monotonic() + tope
    providers.ATTEMPT_DEADLINE.set(fin)
    ultimo = ""
    for clave in claves:
        if time.monotonic() >= fin:
            break
        try:
            return providers.chat(proveedor, clave, modelo, mensajes, max_tokens)
        except Exception as exc:  # noqa: BLE001
            ultimo = str(exc)[:200]
    return {"error": "SIN_RESPUESTA_EN_%dS" % tope if time.monotonic() >= fin else "TODAS_LAS_CLAVES_FALLARON", "detalle": ultimo}


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    p = payload or {}
    try:
        if action == "status":
            return {"status": "ok", "acciones": ["memoria", "env_keys", "base_url", "provider_keys", "chat"]}
        if action == "memoria":
            return _mem_op(p)
        if action == "env_keys":
            from integration.chat_mvp import providers

            return {"status": "ok", "claves": list(providers.env_keys(str(p.get("proveedor") or "")))}
        if action == "base_url":
            from integration.chat_mvp import providers

            return {"status": "ok", "url": providers.base_url(str(p.get("proveedor") or ""))}
        if action == "provider_keys":
            from integration.chat_mvp import vault_hook

            return {"status": "ok", "claves": list(vault_hook.provider_keys(str(p.get("proveedor") or "")))}
        if action == "chat":
            return {"status": "ok", "respuesta": _chat(p)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "reason": type(exc).__name__ + ": " + str(exc)[:200]}
    return {"status": "degraded", "reason": "accion desconocida"}
