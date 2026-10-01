"""Verificador posterior para T07.

Claims del resultado -> comprobaciones reales:
archivo existe, HTTP responde, version coincide, tests pasan,
restricciones/prohibiciones respetadas.
La verificacion NO confia en la afirmacion del ejecutor.
"""
import hashlib
import os
import re
import shlex
import subprocess
import urllib.error
import urllib.request

SIMULADO = os.environ.get("SIMULADO", "") == "1"


def verificar_archivo(ruta):
    """Comprueba que un archivo existe realmente."""
    ok = isinstance(ruta, str) and os.path.isfile(ruta)
    return {"check": "archivo", "target": ruta, "ok": ok,
            "detalle": "existe" if ok else "no existe"}


def verificar_http(url):
    """Comprueba que una URL responde (2xx/3xx). En SIMULADO no hace red."""
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        return {"check": "http", "target": url, "ok": False, "detalle": "url invalida"}
    if SIMULADO:
        ok = url.startswith("http")
        return {"check": "http", "target": url, "ok": ok,
                "detalle": "simulado" if ok else "url invalida"}
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status < 400
            return {"check": "http", "target": url, "ok": ok,
                    "detalle": f"status {resp.status}"}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"check": "http", "target": url, "ok": False, "detalle": str(e)}


def verificar_hash(ruta, esperado):
    if not isinstance(ruta, str) or not isinstance(esperado, str) or not re.fullmatch(r"[0-9a-f]{64}", esperado):
        return {"check": "hash", "target": ruta, "ok": False, "detalle": "hash invalido"}
    try:
        hasher = hashlib.sha256()
        with open(ruta, "rb") as source:
            for chunk in iter(lambda: source.read(65536), b""):
                hasher.update(chunk)
        digest = hasher.hexdigest()
    except (OSError, ValueError, TypeError):
        return {"check": "hash", "target": ruta, "ok": False, "detalle": "fuente no disponible"}
    return {"check": "hash", "target": ruta, "ok": digest == esperado,
            "detalle": "coincide" if digest == esperado else "hash diferente"}


def verificar_version(obtenida, esperada):
    """Comprueba que la version usada coincide con la vigente."""
    ok = bool(obtenida) and str(obtenida) == str(esperada)
    return {"check": "version", "target": str(esperada), "ok": ok,
            "detalle": f"obtenida={obtenida} esperada={esperada}"}


def verificar_tests(comando, cwd=None):
    """Ejecuta los tests de verdad. En SIMULADO no ejecuta nada."""
    if not isinstance(comando, str) or not comando.strip():
        return {"check": "tests", "target": comando, "ok": False,
                "detalle": "comando no proporcionado"}
    if SIMULADO:
        return {"check": "tests", "target": comando, "ok": True,
                "detalle": "simulado: no se ejecuta"}
    try:
        proc = subprocess.run(shlex.split(comando), shell=False, cwd=cwd,
                              capture_output=True, text=True, timeout=120, check=False)
        return {"check": "tests", "target": comando, "ok": proc.returncode == 0,
                "detalle": f"exit {proc.returncode}"}
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        return {"check": "tests", "target": comando, "ok": False, "detalle": str(e)}


def verificar_restricciones(resultado, prohibiciones):
    """Comprueba que el resultado no viola prohibiciones del input."""
    texto = str(resultado).lower()
    violadas = [p for p in prohibiciones if p and p.lower() in texto]
    return {"check": "restricciones", "target": ", ".join(prohibiciones),
            "ok": not violadas,
            "detalle": f"violadas: {violadas}" if violadas else "respetadas"}


def verificar_claims(claims):
    """claims: lista de dicts {tipo, ...}. Devuelve lista de comprobaciones."""
    checks = []
    if not isinstance(claims, list):
        return [{"check": "claim", "target": "", "ok": False, "detalle": "lista invalida"}]
    for c in claims:
        if not isinstance(c, dict):
            checks.append({"check": "claim", "target": "", "ok": False, "detalle": "claim invalido"})
            continue
        tipo = c.get("tipo")
        if tipo == "archivo":
            checks.append(verificar_archivo(c.get("ruta", "")))
        elif tipo == "hash":
            checks.append(verificar_hash(c.get("ruta", ""), c.get("sha256", "")))
        elif tipo == "http":
            checks.append(verificar_http(c.get("url", "")))
        elif tipo == "version":
            checks.append(verificar_version(c.get("obtenida"), c.get("esperada")))
        elif tipo == "tests":
            checks.append(verificar_tests(c.get("comando", ""), c.get("cwd")))
        else:
            checks.append({"check": "claim", "target": str(tipo), "ok": False,
                           "detalle": "tipo no verificable"})
    return checks


def extraer_versiones(texto):
    return re.findall(r"\bv?(\d+\.\d+(?:\.\d+)?)\b", texto or "")
