"""Acciones sobre archivos locales: extraer, copiar, mover, listar, buscar. Todo con sha256 y sin sobrescribir en silencio."""
import hashlib
import os
import shutil
import tarfile
import zipfile
from pathlib import Path

from .seguridad import LIMITE_ARCHIVOS, LIMITE_BYTES, MotorError


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def archivos_de(carpeta):
    """Rutas relativas de todos los archivos regulares (sin .git), ordenadas."""
    base = Path(carpeta)
    if base.is_file():
        return [Path(base.name)]
    return sorted(p.relative_to(base) for p in base.rglob("*") if p.is_file() and not p.is_symlink() and ".git" not in p.relative_to(base).parts)


def es_archivo_comprimido(ruta):
    n = str(ruta).lower()
    return n.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".txz"))


def _limites(cantidad, total):
    if cantidad > LIMITE_ARCHIVOS or total > LIMITE_BYTES:
        raise MotorError("EXTRACCION_EXCEDE_LIMITES")


def _dentro(base, nombre):
    destino = (base / nombre).resolve()
    if destino != base and base not in destino.parents:
        raise MotorError("ZIP_SLIP_BLOQUEADO: " + nombre)
    return destino


def extraer(archivo, destino):
    """Extrae zip/tar a `destino` sin salirse de el; los enlaces simbolicos se omiten. Devuelve (archivos, omitidos)."""
    base = Path(destino).resolve()
    base.mkdir(parents=True, exist_ok=True)
    omitidos, cantidad = [], 0
    if zipfile.is_zipfile(archivo):
        with zipfile.ZipFile(archivo) as z:
            infos = z.infolist()
            _limites(len(infos), sum(i.file_size for i in infos))
            for i in infos:
                destino_i = _dentro(base, i.filename)
                if i.is_dir():
                    destino_i.mkdir(parents=True, exist_ok=True)
                    continue
                if (i.external_attr >> 16) & 0o170000 == 0o120000:
                    omitidos.append(i.filename)
                    continue
                destino_i.parent.mkdir(parents=True, exist_ok=True)
                with z.open(i) as o, open(destino_i, "wb") as f:
                    shutil.copyfileobj(o, f)
                cantidad += 1
        return cantidad, omitidos
    if tarfile.is_tarfile(archivo):
        with tarfile.open(archivo) as t:
            miembros = t.getmembers()
            _limites(len(miembros), sum(m.size for m in miembros))
            for m in miembros:
                destino_m = _dentro(base, m.name)
                if m.isdir():
                    destino_m.mkdir(parents=True, exist_ok=True)
                elif m.isreg():
                    destino_m.parent.mkdir(parents=True, exist_ok=True)
                    with t.extractfile(m) as o, open(destino_m, "wb") as f:
                        shutil.copyfileobj(o, f)
                    cantidad += 1
                else:
                    omitidos.append(m.name)
        return cantidad, omitidos
    raise MotorError("FORMATO_NO_SOPORTADO: " + Path(archivo).name)


def copiar(origen, destino, sobrescribir=False):
    """Copia un archivo o carpeta y comprueba el sha256 de cada archivo. Devuelve [(ruta_relativa, bytes)]."""
    o, d = Path(origen), Path(destino)
    if not o.exists():
        raise MotorError("ORIGEN_NO_EXISTE: " + o.name)
    rels = archivos_de(o)
    base_o = o if o.is_dir() else o.parent
    destinos = [d / r if o.is_dir() else (d / o.name if d.is_dir() else d) for r in rels]
    if not sobrescribir:
        choque = [str(x) for x in destinos if x.exists()]
        if choque:
            raise MotorError("DESTINO_YA_EXISTE: " + choque[0] + " (usa sobrescribir)")
    salida = []
    for rel, dest in zip(rels, destinos):
        fuente = base_o / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fuente, dest)
        if sha256(fuente) != sha256(dest):
            raise MotorError("SHA256_DISTINTO: " + str(rel))
        salida.append((str(rel), dest.stat().st_size))
    return salida


def mover(origen, destino, sobrescribir=False):
    """Copia verificada y solo entonces borra el origen."""
    salida = copiar(origen, destino, sobrescribir)
    o = Path(origen)
    shutil.rmtree(o) if o.is_dir() else o.unlink()
    return salida


def listar(carpeta, maximo=200):
    rels = archivos_de(carpeta)
    base = Path(carpeta) if Path(carpeta).is_dir() else Path(carpeta).parent
    return [(str(r), (base / r).stat().st_size) for r in rels[:maximo]], len(rels)


def buscar(carpeta, patron, maximo=100):
    """Coincidencias en nombres y en el texto de archivos de hasta 1 MB. Devuelve [str]."""
    p = str(patron).lower()
    base = Path(carpeta)
    hallazgos = []
    for rel in archivos_de(base):
        if len(hallazgos) >= maximo:
            break
        if p in str(rel).lower():
            hallazgos.append("nombre: " + str(rel))
            continue
        f = (base / rel) if base.is_dir() else base
        if f.stat().st_size <= 1 << 20:
            try:
                for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if p in linea.lower():
                        hallazgos.append("%s:%d: %s" % (rel, n, linea.strip()[:160]))
                        break
            except (UnicodeDecodeError, OSError):
                continue
    return hallazgos
