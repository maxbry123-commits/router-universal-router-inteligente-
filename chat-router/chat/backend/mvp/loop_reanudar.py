"""Los procesos del LOOP (gobernar, paralelo, motor_ejecutar) sobreviven a un reinicio: se guarda el pedido en el almacen
permanente y, al arrancar, se vuelven a lanzar. El chat sigue preguntando por el proceso_id viejo: ALIAS lo lleva al nuevo."""
import asyncio
from mvp import estado_tarea, loop_puente

ACCIONES = ("gobernar", "ejecutar", "paralelo", "motor_ejecutar")
ALIAS = {}  # proceso_id o grupo_id viejo -> el nuevo


def _ids(r):
    return ([r["proceso_id"]] if r.get("proceso_id") else list(r.get("procesos") or [])), r.get("grupo_id")


def traducir(cuerpo):
    """El chat consulta con el id de antes del reinicio: se cambia por el del proceso retomado."""
    c = dict(cuerpo or {})
    for k in ("proceso_id", "grupo_id"):
        if c.get(k) in ALIAS:
            c[k] = ALIAS[c[k]]
    return c


def _al_terminar(pids, fn):
    """Cuando TODOS los procesos terminan (con o sin error) se ejecuta fn en el hilo que cierra el ultimo."""
    futuros = [f for p in pids if (f := getattr(loop_puente._CARGADOS.get("nct_loop"), "_PROC", {}).get(p)) is not None]
    pendientes = [len(futuros)]
    if not futuros:
        return fn()
    def uno(_f):
        pendientes[0] -= 1
        if pendientes[0] == 0:
            fn()
    for f in futuros:
        f.add_done_callback(uno)


async def registrar(banco, plugin, accion, cuerpo, resultado):
    if plugin != "nct_loop" or accion not in ACCIONES or not isinstance(resultado, dict) or resultado.get("error"):
        return None
    pids, grupo = _ids(resultado)
    if not pids:
        return None
    clave = "loop-" + (grupo or pids[0])
    await asyncio.to_thread(estado_tarea.guardar, banco, clave, {"plugin": plugin, "accion": accion, "cuerpo": cuerpo, "pids": pids, "grupo": grupo})
    await asyncio.to_thread(estado_tarea.marcar, banco, clave, True)
    _al_terminar(pids, lambda: estado_tarea.marcar(banco, clave, False))
    return clave


async def reanudar_todas(banco):
    for clave in [k for k in await asyncio.to_thread(estado_tarea.pendientes, banco) if k.startswith("loop-")]:
        est = await asyncio.to_thread(estado_tarea.leer, banco, clave)
        await asyncio.to_thread(estado_tarea.marcar, banco, clave, False)
        if not est:
            continue
        try:
            nuevo = await loop_puente.llamar(est["plugin"], est["accion"], est["cuerpo"])
        except (OSError, ValueError):
            continue
        if not isinstance(nuevo, dict) or nuevo.get("error"):
            continue
        pids, grupo = _ids(nuevo)
        ALIAS.update(dict(zip(est.get("pids") or [], pids)))
        if est.get("grupo") and grupo:
            ALIAS[est["grupo"]] = grupo
        await registrar(banco, est["plugin"], est["accion"], est["cuerpo"], nuevo)
