"""Limites del motor de archivos: todo vive bajo una raiz; las URL no pueden apuntar a la red interna."""
import ipaddress
import os
import socket
import urllib.parse
import urllib.request
from pathlib import Path

LIMITE_BYTES = int(os.environ.get("RIU_MOTOR_MAX_BYTES", str(4 * 1024 ** 3)))
LIMITE_ARCHIVOS = int(os.environ.get("RIU_MOTOR_MAX_ARCHIVOS", "300000"))
MAX_REDIRECCIONES = 5


class MotorError(Exception):
    """Fallo esperado del motor: el mensaje es el codigo que ve el modelo."""


def raiz():
    r = Path(os.environ.get("RIU_MOTOR_RAIZ") or "/tmp/riu-motor")
    r.mkdir(parents=True, exist_ok=True)
    return r.resolve()


def ruta_segura(texto, base=None):
    """Ruta relativa a la raiz (o absoluta dentro de ella); fuera de la raiz: error."""
    base = (base or raiz()).resolve()
    if not str(texto or "").strip():
        raise MotorError("RUTA_VACIA")
    p = Path(str(texto).strip())
    destino = (p if p.is_absolute() else base / p).resolve()
    if destino != base and base not in destino.parents:
        raise MotorError("RUTA_FUERA_DE_RAIZ: " + str(texto))
    return destino


def _ip_publica(host):
    try:
        direcciones = {i[4][0] for i in socket.getaddrinfo(host, None)}
    except OSError:
        raise MotorError("URL_NO_RESUELVE: " + host) from None
    for d in direcciones:
        ip = ipaddress.ip_address(d.split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise MotorError("URL_RED_INTERNA_BLOQUEADA: " + host)


def url_segura(url):
    u = urllib.parse.urlsplit(str(url).strip())
    if u.scheme not in ("http", "https") or not u.hostname:
        raise MotorError("URL_INVALIDA: solo http o https")
    if not os.environ.get("RIU_MOTOR_PERMITIR_LOCAL"):  # solo las pruebas abren la red local
        _ip_publica(u.hostname)
    return u.geturl()


class _Redirige(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url_segura(newurl)  # cada salto se vuelve a comprobar
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def abrir(url, espera=60):
    url_segura(url)
    req = urllib.request.Request(url, headers={"User-Agent": "riu-motor-archivos"})
    return urllib.request.build_opener(_Redirige).open(req, timeout=espera)
