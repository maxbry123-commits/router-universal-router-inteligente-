"""STORAGE_LIFECYCLE: restore al arrancar + autosync periodico, sobre el Store y el bucket HF existentes.
Solo stdlib. No crea otro almacenamiento. Nunca pisa una base local que ya tenga datos."""
from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable

STATUS: dict[str, Any] = {"restore": "NOT_RUN", "autosync": "OFF", "last_sync": None, "last_error": None}


def restore_if_empty(data_dir: Any, bucket: str | None, token: str | None, fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    d = Path(data_dir)
    db = d / "riu_chat.sqlite3"
    if db.exists() and db.stat().st_size > 0:
        STATUS["restore"] = "SKIPPED_LOCAL_EXISTS"
        return {"status": STATUS["restore"]}
    if not bucket or not token:
        STATUS["restore"] = "SKIPPED_NOT_CONFIGURED"
        return {"status": STATUS["restore"]}
    try:
        if fs_factory is None:
            from huggingface_hub import HfFileSystem as fs_factory  # noqa: N813
        fs = fs_factory(token=token)
        base = f"buckets/{bucket}/riu-chat"
        data = fs.cat_file(f"{base}/riu_chat.sqlite3")
    except Exception as exc:  # noqa: BLE001
        STATUS["restore"] = f"NO_REMOTE_SNAPSHOT:{type(exc).__name__}"
        return {"status": STATUS["restore"]}
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "riu_chat.sqlite3.restore"
    tmp.write_bytes(data)
    esperados: list[str] = []
    try:
        con = sqlite3.connect(tmp)
        ok = con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        if ok:
            try:
                esperados = [r[0] for r in con.execute("SELECT id FROM documents")]
            except Exception:  # noqa: BLE001 - la tabla existe pero la consulta falla = indice invalido: GAP, NO promover
                tiene_docs = con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='documents'").fetchone()[0]
                con.close()
                if tiene_docs:
                    tmp.unlink(missing_ok=True)
                    STATUS["restore"] = "GAP_DOCUMENT_INDEX"
                    return {"status": "GAP_DOCUMENT_INDEX", "gap": "GAP_DOCUMENT_INDEX"}
        con.close()
    except Exception:  # noqa: BLE001
        ok = False
    if not ok:
        tmp.unlink(missing_ok=True)
        STATUS["restore"] = "REMOTE_SNAPSHOT_CORRUPT"
        return {"status": STATUS["restore"]}
    # ATOMICO: el SQLite NO se promueve hasta demostrar que TODOS los documentos registrados existen en el bucket.
    remotos: set[str] = set()
    try:
        for p in fs.ls(f"{base}/docs", detail=False):
            name = str(p).rsplit("/", 1)[-1]
            if name:
                remotos.add(name)
    except FileNotFoundError:  # sin carpeta docs/ en el bucket = cero documentos subidos (caso normal); si SQLite espera alguno, faltantes lo frena abajo
        remotos = set()
    except Exception as exc:  # noqa: BLE001 - sin el listado remoto no se puede demostrar nada: NO promover
        tmp.unlink(missing_ok=True)
        STATUS["restore"] = "GAP_LISTADO_REMOTO:" + type(exc).__name__
        return {"status": STATUS["restore"], "gap": "GAP_LISTADO_REMOTO"}
    faltantes = [did for did in esperados if did not in remotos]
    if faltantes:  # doc registrado en SQLite que falta en el bucket: GAP y la base NO se promueve
        tmp.unlink(missing_ok=True)
        STATUS["restore"] = "GAP_DOCUMENTO_FALTANTE"
        STATUS["docs_gap"] = faltantes
        return {"status": "GAP_DOCUMENTO_FALTANTE", "gap": "GAP_DOCUMENTO_FALTANTE", "faltantes": faltantes}
    docs = 0
    (d / "docs").mkdir(exist_ok=True)
    try:
        for name in remotos:
            if not (d / "docs" / name).exists():
                (d / "docs" / name).write_bytes(fs.cat_file(f"{base}/docs/{name}"))
                docs += 1
    except Exception as exc:  # noqa: BLE001 - un doc no descargado NO promueve la base
        tmp.unlink(missing_ok=True)
        STATUS["restore"] = "GAP_DOC_DESCARGA:" + type(exc).__name__
        return {"status": STATUS["restore"], "gap": "GAP_DOC_DESCARGA"}
    os.replace(tmp, db)  # ultimo paso: ya esta probado integro y con todos sus documentos
    STATUS["restore"] = "RESTORED"
    STATUS["docs_gap"] = []
    return {"status": "RESTORED", "docs": docs}


_thread: threading.Thread | None = None


def _restore_bloquea_sync() -> bool:
    r = str(STATUS.get("restore") or "")
    if r.startswith("NO_REMOTE_SNAPSHOT:"):  # solo "no existe" deja subir; un fallo de red al leer no
        return not r.endswith("FileNotFoundError")
    return r.startswith("GAP_") or r == "REMOTE_SNAPSHOT_CORRUPT"


def start_autosync(get_store: Callable[[], Any], sync_fn: Callable[..., Any], bucket: str | None, token: str | None, interval: float | None = None) -> dict[str, Any]:
    global _thread
    secs = float(os.getenv("RIU_AUTOSYNC_SECONDS", "60")) if interval is None else interval
    if not bucket or not token or secs <= 0:
        STATUS["autosync"] = "OFF_NOT_CONFIGURED"
        return {"status": STATUS["autosync"]}
    if _thread is not None and _thread.is_alive():
        return {"status": "ALREADY_RUNNING"}
    stop = threading.Event()

    def loop() -> None:
        import time
        while not stop.wait(secs):
            if _restore_bloquea_sync():  # hay snapshot remoto que NO se pudo restaurar: subir la base local lo pisaria
                STATUS["last_error"] = "SYNC_BLOQUEADO_RESTORE:" + str(STATUS.get("restore"))
                continue
            try:
                sync_fn(get_store(), bucket, token)
                STATUS["last_sync"] = time.time()
                STATUS["last_error"] = None
            except Exception as exc:  # noqa: BLE001
                STATUS["last_error"] = type(exc).__name__

    _thread = threading.Thread(target=loop, daemon=True, name="riu-autosync")
    _thread.start()
    STATUS["autosync"] = "RUNNING"
    return {"status": "RUNNING", "every_s": secs, "stop": stop}
