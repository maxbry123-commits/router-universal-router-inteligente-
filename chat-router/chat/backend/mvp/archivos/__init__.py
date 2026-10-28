"""Motor de archivos del chat: descargar, extraer, copiar, mover, listar y buscar, en cola, con origen y destino que pone el Director.
Sin Hugging Face, sin LFS, sin GitHub Actions. Un trabajo = {accion, origen, destino, extraer, readme, sobrescribir, patron, max}."""
import json
import shutil
from pathlib import Path

from . import cola, origen as org
from .seguridad import MotorError, raiz, ruta_segura

ACCIONES = ("transferir", "ejecutar", "estado", "cancelar", "raiz", "listar_raiz")


def leer_cola(datos):
    """La cola puede venir como lista de trabajos, texto JSON o texto YAML."""
    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        return [datos]
    texto = str(datos or "").strip()
    if not texto:
        raise MotorError("COLA_VACIA")
    try:
        doc = json.loads(texto)
    except ValueError:
        try:
            import yaml
            doc = yaml.safe_load(texto)
        except ImportError:
            raise MotorError("YAML_NO_DISPONIBLE: envia JSON") from None
        except Exception as e:  # noqa: BLE001
            raise MotorError("YAML_INVALIDO: " + str(e)[:120]) from None
    if isinstance(doc, dict):
        doc = doc.get("cola") or doc.get("trabajos") or doc.get("jobs") or [doc]
    if not isinstance(doc, list):
        raise MotorError("COLA_INVALIDA: debe ser una lista de trabajos")
    return doc


def armar_transferencia(c):
    """Una sola orden -> pasos: listar origen, traerlo al destino (README + sha256) y listar el destino para comprobar."""
    origen, destino = str(c.get("origen") or "").strip(), str(c.get("destino") or "").strip()
    if not origen:
        raise MotorError("ORIGEN_VACIO")
    if not destino:
        raise MotorError("DESTINO_VACIO")
    accion = "copiar" if org.clasificar(origen) == "local" else "descargar"
    extra = {k: c[k] for k in ("extraer", "readme", "sobrescribir") if k in c}
    pasos = [{"accion": "listar", "origen": origen}, {"accion": accion, "origen": origen, "destino": destino, **extra}]
    if not destino.startswith("git:"):
        pasos.append({"accion": "listar", "origen": destino})
    return pasos


def info_raiz():
    r = raiz()
    return {"raiz": str(r), "libre_bytes": shutil.disk_usage(r).free}


def listar_raiz(ruta=""):
    base = ruta_segura(ruta) if str(ruta or "").strip() else raiz()
    if not base.is_dir():
        raise MotorError("NO_ES_CARPETA: " + str(ruta))
    entradas = [{"nombre": p.name, "tipo": "dir" if p.is_dir() else "archivo", "bytes": 0 if p.is_dir() else p.stat().st_size}
                for p in sorted(base.iterdir()) if not p.name.startswith("_")][:500]
    return {"ruta": "" if base == raiz() else base.relative_to(raiz()).as_posix(), "entradas": entradas}


def llamar(accion, cuerpo=None, token=None):
    """Punto de entrada unico (plugin HTTP y herramienta del modelo). Devuelve siempre un dict."""
    c = cuerpo or {}
    try:
        if accion == "transferir":
            pasos = armar_transferencia(c)
            return {**cola.ejecutar(pasos, token), "pasos": pasos}
        if accion == "ejecutar":
            return cola.ejecutar(leer_cola(c.get("cola") or c.get("yaml") or c.get("json") or ([c] if c.get("origen") or c.get("source") else None)), token)
        if accion == "estado":
            return cola.estado(str(c.get("id") or ""))
        if accion == "cancelar":
            return cola.cancelar(str(c.get("id") or ""))
        if accion == "raiz":
            return info_raiz()
        if accion == "listar_raiz":
            return listar_raiz(c.get("ruta", ""))
        raise MotorError("ACCION_INVALIDA: " + str(accion) + " (usa " + ", ".join(ACCIONES) + ")")
    except MotorError as e:
        return {"error": str(e)}
