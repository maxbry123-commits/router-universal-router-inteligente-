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
    try:
        return _restore(data_dir, bucket, token, fs_factory)
    except Exception as exc:  # noqa: BLE001 - un fallo inesperado NO puede dejar "NOT_RUN" (el autosync subiria la base vacia)
        STATUS["restore"] = "GAP_RESTORE_EXC:" + type(exc).__name__
        return {"status": STATUS["restore"], "gap": "GAP_RESTORE_EXC"}


def _restore(data_dir: Any, bucket: str | None, token: str | None, fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    d = Path(data_dir)
    db = d / "riu_chat.sqlite3"
    if db.exists() and db.stat().st_size > 0:
        STATUS["restore"] = "SKIPPED_LOCAL_EXISTS"
        return {"status": STATUS["restore"]}
    if not bucket or not token:
        STATUS["restore"] = "SKIPPED_NOT_CONFIGURED"
        return {"status": STATUS["restore"]}
    tmp = d / "riu_chat.sqlite3.restore"
    r = _bajar(d, tmp, bucket, token, fs_factory)
    if r is not None:
        return r
    os.replace(tmp, db)  # ultimo paso: ya esta probado integro y con todos sus documentos
    STATUS["restore"] = "RESTORED"
    STATUS["docs_gap"] = []
    return {"status": "RESTORED", "docs": STATUS.get("docs_bajados", 0)}


def _bajar(d: Path, tmp: Path, bucket: str, token: str, fs_factory: Callable[..., Any] | None) -> dict[str, Any] | None:
    """Descarga el snapshot a `tmp` y los docs a d/docs; None = listo para usar, dict = estado GAP (tmp borrado)."""
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
    STATUS["docs_bajados"] = docs
    return None


def fusionar(store: Any, remoto: Path) -> dict[str, int]:
    """Funde la base del bucket con lo escrito localmente durante el bloqueo, en la base viva y sin perder filas.
    PK de texto: gana el bucket y la version local distinta queda en fusion_conflictos (nada se pierde). PK entera: las filas del bucket conservan su id y las
    locales que no estan en el bucket (por contenido) se reinsertan con id nuevo. Una sola transaccion."""
    con, n = store._db, {}
    q = lambda cs: ",".join('"%s"' % c for c in cs)  # noqa: E731
    with store._lock:
        if con.in_transaction:
            con.commit()
        con.execute("ATTACH DATABASE ? AS r", (str(remoto),))
        try:
            con.execute("BEGIN IMMEDIATE")
            for name, sql in con.execute("SELECT name, sql FROM r.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
                if not con.execute("SELECT 1 FROM main.sqlite_master WHERE type='table' AND name=?", (name,)).fetchone():
                    con.execute(sql)
                loc = {c[1]: c for c in con.execute('PRAGMA main.table_info("%s")' % name)}
                cols = [c[1] for c in con.execute('PRAGMA r.table_info("%s")' % name) if c[1] in loc]
                pk = [c for c, i in loc.items() if i[5]]
                antes = con.execute('SELECT count(*) FROM main."%s"' % name).fetchone()[0]
                if len(pk) == 1 and str(loc[pk[0]][2]).upper() == "INTEGER":
                    datos = [c for c in loc if c != pk[0]]
                    comun = [c for c in datos if c in cols]
                    cond = " AND ".join('x."%s" IS m."%s"' % (c, c) for c in comun) or "0"
                    solo_local = con.execute('SELECT %s FROM main."%s" m WHERE NOT EXISTS (SELECT 1 FROM r."%s" x WHERE %s) ORDER BY m."%s"'
                                             % (q(datos), name, name, cond, pk[0])).fetchall()
                    con.execute('DELETE FROM main."%s"' % name)
                    con.execute('INSERT INTO main."%s"(%s) SELECT %s FROM r."%s"' % (name, q(cols), q(cols), name))
                    if con.execute("SELECT 1 FROM main.sqlite_master WHERE name='sqlite_sequence'").fetchone():
                        con.execute('UPDATE main.sqlite_sequence SET seq=(SELECT coalesce(max("%s"),0) FROM main."%s") WHERE name=?' % (pk[0], name), (name,))
                    if solo_local:
                        con.executemany('INSERT INTO main."%s"(%s) VALUES(%s)' % (name, q(datos), ",".join("?" * len(datos))), [tuple(r) for r in solo_local])
                elif pk:  # PK de texto: gana la fila del bucket; la version local distinta se archiva en fusion_conflictos
                    on = " AND ".join('m."%s" IS x."%s"' % (c, c) for c in pk)
                    igual = " AND ".join('m."%s" IS x."%s"' % (c, c) for c in cols)
                    con.execute("CREATE TABLE IF NOT EXISTS main.fusion_conflictos(id INTEGER PRIMARY KEY AUTOINCREMENT, tabla TEXT, fila TEXT, ts REAL)")
                    con.execute('INSERT INTO main.fusion_conflictos(tabla,fila,ts) SELECT ?, json_object(%s), strftime(\'%%s\',\'now\') FROM main."%s" m '
                                'JOIN r."%s" x ON %s WHERE NOT (%s)' % (",".join("'%s',m.\"%s\"" % (c, c) for c in loc), name, name, on, igual), (name,))
                    con.execute('INSERT OR REPLACE INTO main."%s"(%s) SELECT %s FROM r."%s"' % (name, q(cols), q(cols), name))
                else:  # sin PK: agrega las filas del bucket que no esten ya (por contenido)
                    cond = " AND ".join('x."%s" IS m."%s"' % (c, c) for c in cols) or "0"
                    con.execute('INSERT INTO main."%s"(%s) SELECT %s FROM r."%s" m WHERE NOT EXISTS (SELECT 1 FROM main."%s" x WHERE %s)'
                                % (name, q(cols), q(cols), name, name, cond))
                n[name] = con.execute('SELECT count(*) FROM main."%s"' % name).fetchone()[0] - antes
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.execute("DETACH DATABASE r")
    return n


def reintentar_restore(store: Any, bucket: str | None, token: str | None, fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Reintento tras un restore fallido: baja el snapshot y lo FUNDE con la base viva; solo entonces desbloquea el sync."""
    try:
        d = Path(store.dir)
        tmp = d / "riu_chat.sqlite3.retry"
        r = _bajar(d, tmp, str(bucket), str(token), fs_factory)
        if r is not None:
            return r  # sigue bloqueado salvo NO_REMOTE_SNAPSHOT:FileNotFoundError (no hay nada que pisar)
        try:
            n = fusionar(store, tmp)
        finally:
            tmp.unlink(missing_ok=True)
        STATUS["restore"] = "RESTORED_MERGED"
        STATUS["merge"] = n
        STATUS["docs_gap"] = []
        return {"status": "RESTORED_MERGED", "merge": n}
    except Exception as exc:  # noqa: BLE001
        STATUS["restore"] = "GAP_RESTORE_EXC:" + type(exc).__name__
        return {"status": STATUS["restore"]}


def _respaldo_pendiente(store: Any, bucket: str, token: str, fecha: str, fs_factory: Callable[..., Any] | None = None) -> None:
    """Mientras el sync esta bloqueado: copia aparte en backups/pendiente-<fecha>.sqlite3 (nunca la base principal)."""
    import tempfile
    try:
        if fs_factory is None:
            from huggingface_hub import HfFileSystem as fs_factory  # noqa: N813
        with tempfile.TemporaryDirectory() as t:
            snap = store.snapshot(Path(t) / "p.sqlite3")
            fs_factory(token=token).pipe_file(f"buckets/{bucket}/backups/pendiente-{fecha}.sqlite3", snap.read_bytes())
        STATUS["pendiente"] = f"backups/pendiente-{fecha}.sqlite3"
    except Exception as exc:  # noqa: BLE001
        STATUS["pendiente_error"] = type(exc).__name__


_thread: threading.Thread | None = None


def _restore_bloquea_sync() -> bool:
    r = str(STATUS.get("restore") or "")
    if r.startswith("NO_REMOTE_SNAPSHOT:"):  # solo "no existe" deja subir; un fallo de red al leer no
        return not r.endswith("FileNotFoundError")
    return r.startswith("GAP_") or r == "REMOTE_SNAPSHOT_CORRUPT"


def start_autosync(get_store: Callable[[], Any], sync_fn: Callable[..., Any], bucket: str | None, token: str | None, interval: float | None = None,
                   fs_factory: Callable[..., Any] | None = None) -> dict[str, Any]:
    global _thread
    secs = float(os.getenv("RIU_AUTOSYNC_SECONDS", "60")) if interval is None else interval
    if not bucket or not token or secs <= 0:
        STATUS["autosync"] = "OFF_NOT_CONFIGURED"
        return {"status": STATUS["autosync"]}
    if _thread is not None and _thread.is_alive():
        return {"status": "ALREADY_RUNNING"}
    stop = threading.Event()
    retry0 = float(os.getenv("RIU_RESTORE_RETRY_SECONDS", "30"))  # backoff 30 -> 45 -> 60 s (tope) + jitter
    pend_s = float(os.getenv("RIU_PENDIENTE_SECONDS", "300"))

    def loop() -> None:
        import random
        import time
        tick = min(secs, 5.0)
        prox_sync = time.time() + secs
        espera, prox_retry, prox_pend, fecha = retry0, 0.0, 0.0, ""
        while not stop.wait(tick):
            ahora = time.time()
            if _restore_bloquea_sync():  # hay snapshot remoto que NO se pudo restaurar: subir la base local lo pisaria
                STATUS["last_error"] = "SYNC_BLOQUEADO_RESTORE:" + str(STATUS.get("restore"))
                try:
                    store = get_store()
                except Exception:  # noqa: BLE001
                    continue
                if not fecha:
                    fecha = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
                    prox_retry, prox_pend = ahora + espera, ahora + min(pend_s, espera)
                if ahora >= prox_retry:
                    STATUS["restore_intentos"] = int(STATUS.get("restore_intentos") or 0) + 1
                    reintentar_restore(store, bucket, token, fs_factory)
                    espera = min(espera * 1.5, max(retry0, 60.0))
                    prox_retry = ahora + espera * random.uniform(0.9, 1.1)
                if _restore_bloquea_sync() and ahora >= prox_pend:
                    _respaldo_pendiente(store, str(bucket), str(token), fecha, fs_factory)
                    prox_pend = ahora + pend_s
                if _restore_bloquea_sync():
                    continue
                prox_sync = 0.0  # recien fundido: subir ya
            if ahora < prox_sync:
                continue
            prox_sync = ahora + secs
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
