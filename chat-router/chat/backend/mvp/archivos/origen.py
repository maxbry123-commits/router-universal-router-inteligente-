"""Origenes: URL (descarga con tope), repositorio GitHub (clon superficial, sin LFS) o ruta local bajo la raiz."""
import hashlib
import os
import re
import subprocess
import urllib.parse
from pathlib import Path

from .seguridad import LIMITE_BYTES, MotorError, abrir, ruta_segura

OWNER = "maxbry123-commits"  # el unico dueno con token propio; el resto se clona anonimo
_GH = re.compile(r"^(?:git:|https?://)?(?:www\.)?(?:github\.com/)?([\w.-]+)/([\w.-]+?)(?:\.git)?(?:@([\w./-]+?))?(?:/(?:tree|blob)/([^/]+))?(?:/(.*))?$")


def clasificar(origen):
    o = str(origen or "").strip()
    if not o:
        raise MotorError("ORIGEN_VACIO")
    if o.startswith("git:") or re.match(r"^(https?://)?(www\.)?github\.com/", o):
        return "git"
    if o.startswith(("http://", "https://")):
        return "url"
    return "local"


def parsear_git(origen):
    """git:owner/repo[@rama][/ruta] o github.com/owner/repo[/tree/rama/ruta] -> (owner, repo, rama|None, ruta)."""
    m = _GH.match(str(origen).strip())
    if not m:
        raise MotorError("GIT_ORIGEN_INVALIDO: " + str(origen))
    owner, repo, rama_arroba, rama_tree, ruta = m.groups()
    return owner, repo, rama_arroba or rama_tree, (ruta or "").strip("/")


def entorno_git(token_fn, owner):
    """Credencial por variable de entorno (nunca en argumentos ni en la URL)."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"}
    if owner == OWNER and token_fn:
        try:
            token = token_fn()
        except Exception:  # noqa: BLE001 - sin token se intenta anonimo
            token = None
        if token:
            env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="credential.helper", MOTOR_TOKEN=token,
                       GIT_CONFIG_VALUE_0='!f() { printf "username=x-access-token\\npassword=%s\\n" "$MOTOR_TOKEN"; }; f')
    return env


def git(args, cwd=None, env=None, espera=900):
    r = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=espera)
    if r.returncode:
        raise MotorError("GIT_FALLO: " + (r.stderr or r.stdout).strip()[-300:].replace(os.environ.get("MOTOR_TOKEN", "\0"), "***"))
    return r.stdout.strip()


def clonar(origen, carpeta, token_fn=None):
    """Clon superficial a `carpeta`; devuelve la ruta de la subcarpeta pedida dentro del clon."""
    if os.environ.get("RIU_MOTOR_PERMITIR_LOCAL") and str(origen).startswith("git:file://"):  # solo pruebas: un repo local
        owner, url, rama, ruta = "", str(origen)[4:], None, ""
    else:
        owner, repo, rama, ruta = parsear_git(origen)
        url = "https://github.com/%s/%s.git" % (owner, repo)
    args = ["clone", "--depth", "1", "--single-branch", *(["--branch", rama] if rama else []), url, str(carpeta)]
    git(args, env=entorno_git(token_fn, owner))
    destino = (Path(carpeta) / ruta).resolve() if ruta else Path(carpeta)
    if not destino.exists() or Path(carpeta).resolve() not in [destino, *destino.parents]:
        raise MotorError("GIT_RUTA_NO_EXISTE: " + ruta)
    return destino


def nombre_de(url):
    n = Path(urllib.parse.urlsplit(url).path).name
    return re.sub(r"[^\w.\-]", "_", urllib.parse.unquote(n)) or "descarga"


def descargar(url, carpeta, cancelado=lambda: False):
    """Descarga en streaming con tope de bytes. Devuelve (ruta, bytes, sha256)."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    h, total = hashlib.sha256(), 0
    with abrir(url) as r:
        nombre = nombre_de(r.geturl() or url)
        destino = carpeta / nombre
        with open(destino, "wb") as f:
            for bloque in iter(lambda: r.read(1 << 20), b""):
                if cancelado():
                    raise MotorError("CANCELADO")
                total += len(bloque)
                if total > LIMITE_BYTES:
                    raise MotorError("DESCARGA_EXCEDE_LIMITE")
                h.update(bloque)
                f.write(bloque)
    return destino, total, h.hexdigest()


def local(origen):
    p = ruta_segura(origen)
    if not p.exists():
        raise MotorError("ORIGEN_NO_EXISTE: " + str(origen))
    return p
