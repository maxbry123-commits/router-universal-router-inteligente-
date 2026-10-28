"""Destino GitHub: copia fiel (blobs identicos, sin filtros ni LFS), lotes pequenos, push sin force y lectura de vuelta."""
import os
import re
import subprocess
from pathlib import Path

from .acciones import archivos_de
from .origen import OWNER, entorno_git, git
from .seguridad import MotorError

LOTE_BYTES = 200 * 1024 * 1024
_ID = {"GIT_AUTHOR_NAME": "RIU motor de archivos", "GIT_AUTHOR_EMAIL": "motor@riu.local", "GIT_COMMITTER_NAME": "RIU motor de archivos", "GIT_COMMITTER_EMAIL": "motor@riu.local"}


def parsear(destino):
    """git:owner/repo[@rama]/carpeta -> (owner, repo, rama, carpeta). Solo el dueno del Router."""
    m = re.match(r"^git:([\w.-]+)/([\w.-]+?)(?:@([\w.-]+))?(?:/(.+))?$", str(destino).strip())
    if not m:
        raise MotorError("DESTINO_GIT_INVALIDO: usa git:owner/repo[@rama]/carpeta")
    owner, repo, rama, carpeta = m.groups()
    if owner != OWNER:
        raise MotorError("DESTINO_GIT_SOLO_CUENTA_DEL_ROUTER: " + OWNER)
    return owner, repo, rama, (carpeta or "").strip("/")


def url_remota(owner, repo):
    base = os.environ.get("RIU_MOTOR_GIT_BASE") if os.environ.get("RIU_MOTOR_PERMITIR_LOCAL") else None  # solo pruebas: un remoto local
    return "%s/%s/%s.git" % (base or "https://github.com", owner, repo)


def _lotes(rels, base):
    lote, peso = [], 0
    for r in rels:
        n = (base / r).stat().st_size
        if lote and peso + n > LOTE_BYTES:
            yield lote
            lote, peso = [], 0
        lote.append(r)
        peso += n
    if lote:
        yield lote


def _oid(clon, ruta, env):
    return git(["hash-object", "-w", "--no-filters", str(ruta)], cwd=clon, env=env)


def publicar(fuente, destino, mensaje, token_fn=None, sobrescribir=False, cancelado=lambda: False):
    owner, repo, rama, carpeta = parsear(destino)
    env = {**entorno_git(token_fn, owner), **_ID}
    if "MOTOR_TOKEN" not in env:
        raise MotorError("GITHUB_TOKEN_NO_DISPONIBLE")
    import tempfile
    with tempfile.TemporaryDirectory(prefix="motor-git-") as tmp:
        clon = Path(tmp) / "repo"
        git(["clone", "--depth", "1", *(["--branch", rama] if rama else []), url_remota(owner, repo), str(clon)], env=env)
        rama = rama or git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=clon, env=env)
        fuente = Path(fuente)
        base = fuente if fuente.is_dir() else fuente.parent
        rels = archivos_de(fuente)
        previos = [r for r in rels if (clon / carpeta / r).exists()]
        if previos and not sobrescribir:
            raise MotorError("DESTINO_YA_EXISTE: %s/%s (usa sobrescribir)" % (carpeta, previos[0]))
        total = 0
        for n, lote in enumerate(_lotes(rels, base), 1):
            if cancelado():
                raise MotorError("CANCELADO")
            entradas = []
            for r in lote:
                destino_r = clon / carpeta / r
                destino_r.parent.mkdir(parents=True, exist_ok=True)
                destino_r.write_bytes((base / r).read_bytes())
                rel_repo = (Path(carpeta) / r).as_posix() if carpeta else r.as_posix()
                entradas.append("100644 %s\t%s" % (_oid(clon, destino_r, env), rel_repo))
            subprocess.run(["git", "update-index", "--add", "--index-info"], cwd=clon, env=env, input="\n".join(entradas) + "\n", text=True, check=True, capture_output=True)
            git(["commit", "-q", "-m", "%s (lote %d)" % (mensaje, n)], cwd=clon, env=env)
            git(["push", "-q", "origin", "HEAD:" + rama], cwd=clon, env=env)
            total += len(lote)
        cabeza = git(["rev-parse", "HEAD"], cwd=clon, env=env)
        remoto = git(["ls-remote", "origin", "refs/heads/" + rama], cwd=clon, env=env).split()[0]
        if remoto != cabeza:
            raise MotorError("READ_BACK_DISTINTO: el remoto no coincide con el commit local")
        return {"commit": cabeza[:10], "archivos": total, "repo": "%s/%s" % (owner, repo), "rama": rama, "carpeta": carpeta}
