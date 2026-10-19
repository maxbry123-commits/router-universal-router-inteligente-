# DSL G17 — DISPARADOR POR HORARIO (dentro del Router existente; sin servidor nuevo, sin Actions)
# Hilo que cada 30 s revisa fichas/programas.json; si toca -> lanza el objetivo por el mismo
# camino de chat_async (sesion "programa-<id>"). Guarda "ultima_ejecucion" en SQLite para no
# repetir; al reiniciar el Router, si se perdio una ejecucion en las ultimas 6 h la corre una vez.
# Un programa no se lanza si su ejecucion anterior sigue corriendo.
import json
import threading
import time
from pathlib import Path

_HILO = None
_CORRIENDO: set = set()  # ids de programa con ejecucion en curso (nunca dos a la vez)
CADA_S = 30
CATCHUP_S = 6 * 3600


def _dir_fichas():
    return Path(__file__).resolve().parent.parent / 'fichas'


def _programas():
    try:
        return json.loads((_dir_fichas() / 'programas.json').read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return []


def _ultima(db, pid):
    try:
        r = db.execute('SELECT data FROM memoria_yaiwes WHERE key=? ORDER BY id DESC LIMIT 1',
                       ('programa:' + pid,)).fetchone()
        return float((json.loads(r[0]) or {}).get('ts') or 0) if r else 0.0
    except Exception:  # noqa: BLE001
        return 0.0


def _marcar(db, pid):
    try:
        db.execute('INSERT INTO memoria_yaiwes (scope, key, data) VALUES (?,?,?)',
                   ('programas', 'programa:' + pid, json.dumps({'ts': time.time()})))
        db.commit()
    except Exception:  # noqa: BLE001
        pass


def _toca(prog, ahora, ultima):
    cu = prog.get('cuando') or {}
    if cu.get('cada_min'):
        return (ahora - ultima) >= float(cu['cada_min']) * 60
    if cu.get('diario'):
        try:
            hh, mm = (int(x) for x in str(cu['diario']).split(':')[:2])
            # DSL A10.2: ultima ocurrencia programada en la zona del programa; toca si ya paso y no se lanzo
            import datetime as _dt  # noqa: PLC0415
            try:
                from zoneinfo import ZoneInfo  # noqa: PLC0415
                tz = ZoneInfo(str(prog.get('zona') or 'UTC'))
            except Exception:  # noqa: BLE001
                tz = _dt.timezone.utc
            ahora_z = _dt.datetime.fromtimestamp(ahora, tz)
            ult_prog = ahora_z.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if ult_prog.timestamp() > ahora:
                ult_prog -= _dt.timedelta(days=1)
            # dentro de la ventana catch-up y sin lanzar desde esa ocurrencia
            return ult_prog.timestamp() <= ahora < ult_prog.timestamp() + CATCHUP_S and ultima < ult_prog.timestamp()
        except Exception:  # noqa: BLE001
            return False
    return False


def _lanzar(prog, chat_fn, pid):
    _CORRIENDO.add(pid)
    try:
        obj_ref = str(prog.get('objetivo_ref') or '')
        obj = {'objetivo': obj_ref, 'ficha': str(prog.get('ficha') or '1'),
               'modelo': str(prog.get('modelo') or 'ficha-qwen38flash'),
               'modo_por_defecto': prog.get('modo_por_defecto') or 'code'}
        try:  # objetivo_ref puede ser un archivo .json en el repo
            _f = Path(__file__).resolve().parent.parent.parent.parent.parent / obj_ref
            if _f.is_file():
                obj.update(json.loads(_f.read_text(encoding='utf-8')))
        except Exception:  # noqa: BLE001
            pass
        chat_fn({'ficha_qwen': obj.get('ficha'), 'message': obj.get('objetivo'),
                 'modelo': obj.get('modelo'), 'objetivo': obj, 'task_type': 'code',
                 'sesion': 'programa-' + str(pid)})
    finally:
        _CORRIENDO.discard(pid)


def _bucle(chat_fn, db_fn):
    while True:
        try:
            ahora = time.time()
            for prog in _programas():
                if not prog.get('activo') or not prog.get('id'):
                    continue
                pid = str(prog['id'])
                if pid in _CORRIENDO:
                    continue
                db = db_fn() if callable(db_fn) else db_fn
                ult = _ultima(db, pid) if db is not None else 0.0
                if _toca(prog, ahora, ult):
                    if db is not None:
                        _marcar(db, pid)
                    threading.Thread(target=_lanzar, args=(prog, chat_fn, pid), daemon=True).start()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(CADA_S)


def arrancar(chat_fn, db_fn):
    global _HILO
    if _HILO is not None:
        return
    _HILO = threading.Thread(target=_bucle, args=(chat_fn, db_fn), daemon=True, name='riu-programador')
    _HILO.start()
