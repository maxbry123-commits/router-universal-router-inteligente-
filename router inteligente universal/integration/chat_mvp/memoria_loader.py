"""Single Router loader for the memory_yaiwes package."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import base64
import binascii
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .router import _auth, get_store

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = ROOT / "chat router" / "04-MEMORIA" / "memoria_yaiwes"
_facade: Any = None
_store_id: int | None = None


def _memory() -> Any:
    global _facade, _store_id
    store = get_store()
    if _facade is None or _store_id != id(store):
        init = PACKAGE_DIR / "__init__.py"
        spec = importlib.util.spec_from_file_location("memoria_yaiwes", init, submodule_search_locations=[str(PACKAGE_DIR)])
        if spec is None or spec.loader is None:
            raise RuntimeError("MEMORIA_PACKAGE_LOAD_FAILED")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _facade = module.build_memory(store)
        _store_id = id(store)
    return _facade


CHAT_OWNER = "chat-ui"  # = plugins/puente_chat/plugin.py DUENO: puente_chat guarda cada turno en scope chat-ui:chat:<sesion>
_SESION = re.compile(r"^[A-Za-z0-9_.:@-]{1,60}$")


def chat_history(sesion: str, limit: int = 200) -> dict[str, Any]:
    """Messages of ONE chat, oldest first, read from the canonical SQLite memory (turno-<ms> records of puente_chat).

    The same SQLite file is snapshotted to the HF bucket by storage autosync and restored on Job start, so the
    history survives a Job switch. Checkpoints and other records of the scope are not returned.
    """
    from .memory_runtime import scope_for
    scope = scope_for(CHAT_OWNER, "chat:" + sesion)
    rows = _memory().sqlite.search(scope, "turno-", max(1, min(int(limit), 1000)))
    turns = [r for r in rows if str(r.get("key", "")).startswith("turno-")]
    turns.sort(key=lambda r: r["id"])
    messages: list[dict[str, Any]] = []
    for r in turns:
        d = r.get("data") or {}
        try:
            ts = int(str(r["key"])[6:]) / 1000.0
        except ValueError:
            ts = None
        if d.get("pregunta"):
            messages.append({"role": "user", "content": str(d["pregunta"]), "ts": ts})
        messages.append({"role": "assistant", "content": str(d.get("respuesta", "")), "model": d.get("modelo"), "ts": ts})
    return {"sesion": sesion, "scope": scope, "turns": len(turns), "messages": messages}


# --- PUNTO 4: archivos por chat. Mismo mecanismo que la accion puente_chat "subir": registro 'archivo:<nombre>'
# en la memoria SQLite del chat (scope chat-ui:chat:<sesion>), que el autosync sube al bucket y el arranque restaura.
FILE_MAX_B64 = 4_000_000  # el limite que ya tenia "subir" (~3 MB decodificados)
_TIPO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]*/[A-Za-z0-9][A-Za-z0-9.+-]*$")
_BAD_NAME = re.compile(r"[\x00-\x1f\x7f/\\]")


class FileError(ValueError):
    def __init__(self, code: str, status: int) -> None:
        super().__init__(code)
        self.code, self.status = code, status


def clean_file_name(nombre: Any) -> str:
    """Nombre de archivo seguro: sin rutas, sin '..', sin control, 1-120 caracteres."""
    n = str(nombre or "").strip()
    if not n or len(n) > 120 or _BAD_NAME.search(n) or n in (".", "..") or ".." in n:
        raise FileError("NOMBRE_INVALIDO", 422)
    return n


def _file_scope(sesion: str) -> str:
    from .memory_runtime import scope_for
    return scope_for(CHAT_OWNER, "chat:" + sesion)


def save_chat_file(sesion: str, nombre: Any, tipo: Any, datos_b64: Any) -> dict[str, Any]:
    n = clean_file_name(nombre)
    datos = str(datos_b64 or "")
    if len(datos) > FILE_MAX_B64:
        raise FileError("ARCHIVO_MUY_GRANDE", 413)
    try:
        raw = base64.b64decode(datos, validate=True)
    except (binascii.Error, ValueError):
        raise FileError("BASE64_INVALIDO", 422) from None
    t = str(tipo or "")[:80]
    saved = _memory().save(_file_scope(sesion), "archivo:" + n, {"nombre": n, "tipo": t, "datos_b64": datos})
    return {"ok": True, "file_id": saved.get("id"), "nombre": n, "tipo": t, "bytes": len(raw)}


def _file_rows(scope: str) -> list[Any]:
    db = _memory().sqlite.db
    return db.execute("SELECT id,key,data,created_at FROM memoria_yaiwes WHERE scope=? AND substr(key,1,8)='archivo:' ORDER BY id DESC",
                      (scope,)).fetchall()


def list_chat_files(sesion: str) -> dict[str, Any]:
    """Ultima version de cada nombre (re-subir un nombre lo reemplaza, como en la accion 'archivos')."""
    files, seen = [], set()
    for row in _file_rows(_file_scope(sesion)):
        if row["key"] in seen:
            continue
        seen.add(row["key"])
        d = json.loads(row["data"]) if row["data"] else {}
        b64 = str(d.get("datos_b64") or "")
        files.append({"file_id": row["id"], "nombre": d.get("nombre") or row["key"][8:], "tipo": d.get("tipo") or "",
                      "bytes": max(0, len(b64) * 3 // 4 - b64[-2:].count("=")), "ts": row["created_at"]})
    return {"sesion": sesion, "files": files}


def _file_row(sesion: str, file_id: int) -> Any:
    db = _memory().sqlite.db
    row = db.execute("SELECT id,key,data FROM memoria_yaiwes WHERE id=? AND scope=? AND substr(key,1,8)='archivo:'",
                     (int(file_id), _file_scope(sesion))).fetchone()
    if row is None:
        raise FileError("ARCHIVO_NO_EXISTE", 404)
    return row


def read_chat_file(sesion: str, file_id: int) -> tuple[str, str, bytes]:
    d = json.loads(_file_row(sesion, file_id)["data"])
    tipo = str(d.get("tipo") or "")
    return str(d.get("nombre") or "archivo"), (tipo if _TIPO.match(tipo) else "application/octet-stream"), base64.b64decode(d.get("datos_b64") or "")


def delete_chat_file(sesion: str, file_id: int) -> dict[str, Any]:
    """Borra todas las versiones de ese nombre en ESE chat (si no, reapareceria la anterior) y su nodo del grafo."""
    row = _file_row(sesion, file_id)
    scope, key = _file_scope(sesion), row["key"]
    mem = _memory()
    cur = mem.sqlite.db.execute("DELETE FROM memoria_yaiwes WHERE scope=? AND key=?", (scope, key))
    mem.sqlite.db.commit()
    store = get_store()
    node = "memory:%s:%s" % (scope, key)
    store._exec("DELETE FROM graph_nodes WHERE id=?", (node,))
    store._exec("DELETE FROM graph_edges WHERE src=? OR dst=?", (node, node))
    return {"deleted": int(file_id), "nombre": key[8:], "versions": cur.rowcount}


class FileUpload(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo: str = Field(default="", max_length=80)
    datos_b64: str = Field(min_length=0, max_length=FILE_MAX_B64 + 4)


class MemorySave(BaseModel):
    scope: str = Field(min_length=1, max_length=80)
    key: str = Field(min_length=1, max_length=200)
    data: Any


def build_memory_router() -> APIRouter:
    router = APIRouter()

    @router.get("/memoria/health")
    def health(_owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return _memory().health()
        except Exception as exc:  # noqa: BLE001 - fail closed without taking Router down
            return {"schema": "yaiwes.memory/v1", "fallback": "sqlite", "status": "GAP", "error": type(exc).__name__}

    @router.post("/memoria/save")
    def save(req: MemorySave, _owner: str = Depends(_auth)) -> dict[str, Any]:
        try:
            return _memory().save(req.scope, req.key, req.data)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="MEMORY_SAVE_INVALID") from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail="MEMORY_SAVE_UNAVAILABLE") from exc

    @router.get("/memoria/load")
    def load(scope: str, key: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"scope": scope, "key": key, "records": _memory().load(scope, key)}

    @router.get("/memoria/search")
    def search(scope: str, query: str, k: int = 10, _owner: str = Depends(_auth)) -> dict[str, Any]:
        return {"scope": scope, "query": query, "results": _memory().search(scope, query, max(1, min(k, 100)))}

    @router.get("/chat/history/{sesion}")
    def history(sesion: str, limit: int = 200, _owner: str = Depends(_auth)) -> dict[str, Any]:
        """Persistent history of one chat (sesion = chat_id, e.g. web-<16hex>). Only that chat's messages."""
        if not _SESION.match(sesion):
            raise HTTPException(status_code=422, detail="SESION_INVALIDA")
        try:
            return chat_history(sesion, limit)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail="HISTORY_UNAVAILABLE") from exc

    def _check(sesion: str) -> None:
        if not _SESION.match(sesion):
            raise HTTPException(status_code=422, detail="SESION_INVALIDA")

    def _files(fn: Any, *args: Any) -> Any:
        try:
            return fn(*args)
        except FileError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.code) from exc

    @router.get("/chat/files/{sesion}")
    def files_list(sesion: str, _owner: str = Depends(_auth)) -> dict[str, Any]:
        _check(sesion)
        return list_chat_files(sesion)

    @router.post("/chat/files/{sesion}")
    def files_upload(sesion: str, req: FileUpload, _owner: str = Depends(_auth)) -> dict[str, Any]:
        _check(sesion)
        return _files(save_chat_file, sesion, req.nombre, req.tipo, req.datos_b64)

    @router.get("/chat/files/{sesion}/{file_id}")
    def files_get(sesion: str, file_id: int, _owner: str = Depends(_auth)) -> Response:
        _check(sesion)
        nombre, tipo, raw = _files(read_chat_file, sesion, file_id)
        return Response(raw, media_type=tipo, headers={  # siempre descarga: nunca se sirve HTML inline desde el Router
            "Content-Disposition": "attachment; filename*=UTF-8''" + quote(nombre, safe=""),
            "X-Content-Type-Options": "nosniff"})

    @router.delete("/chat/files/{sesion}/{file_id}")
    def files_delete(sesion: str, file_id: int, _owner: str = Depends(_auth)) -> dict[str, Any]:
        _check(sesion)
        return _files(delete_chat_file, sesion, file_id)

    return router
