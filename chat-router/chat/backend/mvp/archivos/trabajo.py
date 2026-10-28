"""Un trabajo de la cola: origen -> (lista) -> destino, con README y verificacion."""
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from . import acciones, destino_git, origen as org, readme
from .seguridad import MotorError, raiz, ruta_segura

ACCIONES = ("descargar", "extraer", "copiar", "mover", "listar", "buscar")
SINONIMOS = {"accion": ("accion", "action", "op"), "origen": ("origen", "source", "origin", "url", "src", "desde"),
             "destino": ("destino", "dest", "destination", "to", "hacia")}


def normalizar(t):
    """Acepta nombres en espanol o ingles; devuelve el trabajo con claves canonicas y valores por defecto."""
    if not isinstance(t, dict):
        raise MotorError("TRABAJO_INVALIDO: cada trabajo debe ser un objeto")
    out = dict(t)
    for clave, alias in SINONIMOS.items():
        for a in alias:
            if t.get(a) not in (None, ""):
                out[clave] = t[a]
                break
    accion = str(out.get("accion") or "descargar").lower()
    if accion not in ACCIONES:
        raise MotorError("ACCION_INVALIDA: " + accion + " (usa " + ", ".join(ACCIONES) + ")")
    if not out.get("origen"):
        raise MotorError("ORIGEN_VACIO")
    out["accion"] = accion
    out.setdefault("extraer", True)
    out.setdefault("readme", True)
    out.setdefault("sobrescribir", False)
    out["max"] = int(out.get("max") or 200)
    return out


def _slug(origen):
    base = re.sub(r"\.(zip|tar|tgz|gz|bz2|xz|git)$", "", Path(str(origen).rstrip("/").split("?")[0]).name, flags=re.I)
    return re.sub(r"[^\w.\-]", "_", base) or "descarga"


def _traer(job, tmp, ctx):
    """Deja el origen en `tmp` (o devuelve la ruta local). Devuelve (ruta, descripcion)."""
    tipo = org.clasificar(job["origen"])
    if tipo == "local":
        return org.local(job["origen"]), "local"
    if tipo == "git":
        return org.clonar(job["origen"], tmp / "clon", ctx.get("token")), "git"
    archivo, n, sha = org.descargar(job["origen"], tmp / "descarga", ctx["cancelado"])
    if job["extraer"] and acciones.es_archivo_comprimido(archivo):
        carpeta = tmp / "extraido"
        cantidad, omitidos = acciones.extraer(archivo, carpeta)
        ctx["notas"].append("extraidos %d archivos%s" % (cantidad, (", omitidos %d enlaces" % len(omitidos)) if omitidos else ""))
        return carpeta, "url+extraccion"
    ctx["notas"].append("sha256 %s" % sha[:16])
    return archivo, "url"


def _escribir(fuente, job, ctx):
    destino = job.get("destino") or _slug(job["origen"])
    if str(destino).startswith("git:"):
        return destino_git.publicar(fuente, destino, "motor de archivos: " + job["accion"], ctx.get("token"), job["sobrescribir"], ctx["cancelado"]), destino
    ruta = ruta_segura(destino)
    copiado = acciones.copiar(fuente, ruta, job["sobrescribir"])
    if job["readme"] and ruta.is_dir():
        ctx["notas"].append("readme: " + str(readme.escribir(ruta, job["origen"], job["accion"])))
    return copiado, str(ruta.relative_to(raiz()))


def _listar_comprimido(archivo, maximo):
    with zipfile.ZipFile(archivo) as z:
        nombres = [i for i in z.infolist() if not i.is_dir()]
        return [(i.filename, i.file_size) for i in nombres[:maximo]], len(nombres)


def ejecutar(job, ctx):
    """Corre un trabajo normalizado. Devuelve {archivos, bytes, resumen, muestra, destino}."""
    ctx["notas"] = []
    (raiz() / "_tmp").mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="trabajo-", dir=raiz() / "_tmp"))
    try:
        if job["accion"] in ("listar", "buscar"):
            fuente, _ = _traer({**job, "extraer": False}, tmp, ctx)
            if job["accion"] == "buscar":
                carpeta = _traer({**job, "extraer": True}, tmp / "b", ctx)[0] if fuente.is_file() and acciones.es_archivo_comprimido(fuente) else fuente
                hallazgos = acciones.buscar(carpeta, job.get("patron") or "", job["max"])
                return {"archivos": len(hallazgos), "bytes": 0, "resumen": "%d coincidencias" % len(hallazgos), "muestra": hallazgos[:20]}
            lista, total = _listar_comprimido(fuente, job["max"]) if fuente.is_file() and zipfile.is_zipfile(fuente) else acciones.listar(fuente, job["max"])
            return {"archivos": total, "bytes": sum(b for _, b in lista), "resumen": "%d archivos (se muestran %d)" % (total, len(lista)), "muestra": [n for n, _ in lista[:20]]}
        if job["accion"] == "extraer":
            fuente, _ = _traer({**job, "extraer": False}, tmp, ctx)
            if not (fuente.is_file() and acciones.es_archivo_comprimido(fuente)):
                raise MotorError("NO_ES_COMPRIMIDO: " + str(job["origen"]))
            nuevo = tmp / "extraido"
            acciones.extraer(fuente, nuevo)
            copiado, destino = _escribir(nuevo, job, ctx)
        else:
            fuente, _ = _traer(job, tmp, ctx)
            if job["accion"] == "mover" and org.clasificar(job["origen"]) != "local":
                raise MotorError("MOVER_SOLO_LOCAL: usa descargar para URL o git")
            copiado, destino = _escribir(fuente, job, ctx)
            if job["accion"] == "mover":
                shutil.rmtree(fuente) if fuente.is_dir() else fuente.unlink()
        if isinstance(copiado, dict):
            return {"archivos": copiado["archivos"], "bytes": 0, "resumen": "publicado %s@%s (%s)" % (copiado["repo"], copiado["rama"], copiado["commit"]), "muestra": [], "destino": destino}
        return {"archivos": len(copiado), "bytes": sum(b for _, b in copiado), "resumen": "; ".join(ctx["notas"]) or "ok", "muestra": [r for r, _ in copiado[:20]], "destino": destino}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
