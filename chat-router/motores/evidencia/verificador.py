"""Verificador posterior para T07.

Claims del resultado -> comprobaciones reales:
archivo existe, HTTP responde, version coincide, tests pasan,
restricciones/prohibiciones respetadas.
La verificacion NO confia en la afirmacion del ejecutor.
"""
import os
import re
import subprocess
import urllib.request

SIMULADO = os.environ.get("SIMULADO", "") == "1"


def verificar_archivo(ruta):
    """Comprueba que un archivo existe realmente."""
    ok = os.path.exists(ruta)
    return {"check": "archivo", "target": ruta, "ok": ok,
            "detalle": "existe" if ok else "no existe"}


def verificar_http(url):
    """Comprueba que una URL responde (2xx/3xx). En SIMULADO no hace red."""
    if SIMULADO:
        ok = url.startswith("http")
        return {"check": "http", "target": url, "ok": ok,
                "detalle": "simulado" if ok else "url invalida"}
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status < 400
            return {"check": "http", "target": url, "ok": ok,
                    "detalle": "status %d" % resp.status}
    except Exception as e:
        return {"check": "http", "target": url, "ok": False, "detalle": str(e)}


def verificar_version(obtenida, esperada):
    """Comprueba que la version usada coincide con la vigente."""
    ok = bool(obtenida) and str(obtenida) == str(esperada)
    return {"check": "version", "target": str(esperada), "ok": ok,
            "detalle": "obtenida=%s esperada=%s" % (obtenida, esperada)}


def verificar_tests(comando, cwd=None):
    """Ejecuta los tests de verdad. En SIMULADO no ejecuta nada."""
    if SIMULADO:
        return {"check": "tests", "target": comando, "ok": True,
                "detalle": "simulado: no se ejecuta"}
    try:
        proc = subprocess.run(comando, shell=True, cwd=cwd,
                              capture_output=True, text=True, timeout=120)
        return {"check": "tests", "target": comando, "ok": proc.returncode == 0,
                "detalle": "exit %d" % proc.returncode}
    except Exception as e:
        return {"check": "tests", "target": comando, "ok": False, "detalle": str(e)}


def verificar_restricciones(resultado, prohibiciones):
    """Comprueba que el resultado no viola prohibiciones del input."""
    texto = str(resultado).lower()
    violadas = [p for p in prohibiciones if p and p.lower() in texto]
    return {"check": "restricciones", "target": ", ".join(prohibiciones),
            "ok": not violadas,
            "detalle": "violadas: %s" % violadas if violadas else "respetadas"}


def verificar_claims(claims):
    """claims: lista de dicts {tipo, ...}. Devuelve lista de comprobaciones."""
    checks = []
    for c in claims or []:
        tipo = c.get("tipo")
        if tipo == "archivo":
            checks.append(verificar_archivo(c.get("ruta", "")))
        elif tipo == "http":
            checks.append(verificar_http(c.get("url", "")))
        elif tipo == "version":
            checks.append(verificar_version(c.get("obtenida"), c.get("esperada")))
        elif tipo == "tests":
            checks.append(verificar_tests(c.get("comando", ""), c.get("cwd")))
    return checks


def extraer_versiones(texto):
    return re.findall(r"\bv?(\d+\.\d+(?:\.\d+)?)\b", texto or "")
