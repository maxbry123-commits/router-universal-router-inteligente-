import os
import re
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
import httpx

HOSTS_PERMITIDOS = {"github.com", "codeload.github.com", "huggingface.co", "api.github.com"}
MAX_BYTES = 200 * 1024 * 1024
TOP_N = 10

def _raiz(tipo: str) -> Path:
    if tipo == "skills":
        return Path(os.getenv("SKILLS_DIR", "skills"))
    if tipo == "componentes":
        return Path(os.getenv("COMPONENTES_DIR", "componentes_descargados"))
    raise ValueError(f"destino desconocido: {tipo}")

def _host_ok(url: str) -> bool:
    m = re.match(r"https://([^/]+)/", url)
    return bool(m) and m.group(1).lower() in HOSTS_PERMITIDOS

def _nombre(url: str) -> str:
    partes = re.sub(r"\.git$", "", url.rstrip("/")).split("/")
    return "__".join(partes[-2:]) if len(partes) >= 2 else partes[-1]

def buscar_github(query: str, n: int = TOP_N, client=None) -> list:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    c = client or httpx.Client(timeout=20)
    r = c.get("https://api.github.com/search/repositories", params={"q": query, "sort": "stars", "per_page": min(n, 10)}, headers=headers)
    if r.status_code >= 400:
        return []
    return [{"url": i["html_url"], "stars": i.get("stargazers_count", 0), "desc": i.get("description") or ""} for i in r.json().get("items", [])][:n]

def buscar_huggingface(query: str, n: int = TOP_N, client=None) -> list:
    c = client or httpx.Client(timeout=20)
    r = c.get("https://huggingface.co/api/models", params={"search": query, "sort": "downloads", "limit": min(n, 10)})
    if r.status_code >= 400:
        return []
    return [{"url": f"https://huggingface.co/{i['id']}", "stars": i.get("downloads", 0), "desc": i.get("id", "")} for i in r.json()][:n]

def descargar_repo(url: str, tipo: str) -> dict:
    if not _host_ok(url):
        return {"status": "failed", "error": "host no permitido"}
    destino = _raiz(tipo) / _nombre(url)
    if destino.exists():
        return {"status": "ok", "ruta": str(destino), "accion": "ya_existe"}
    destino.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1", "GIT_TERMINAL_PROMPT": "0"}
    p = subprocess.run(["git", "clone", "--depth", "1", url, str(destino)], env=env, capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        shutil.rmtree(destino, ignore_errors=True)
        return {"status": "failed", "error": p.stderr[-300:]}
    shutil.rmtree(destino / ".git", ignore_errors=True)
    return {"status": "ok", "ruta": str(destino), "accion": "clonado"}

def descargar_archivo(url: str, tipo: str, client=None) -> dict:
    if not _host_ok(url):
        return {"status": "failed", "error": "host no permitido"}
    destino_dir = _raiz(tipo) / _nombre(url)
    destino_dir.mkdir(parents=True, exist_ok=True)
    c = client or httpx.Client(timeout=120, follow_redirects=True)
    ruta = destino_dir / "paquete"
    with c.stream("GET", url) as r:
        if r.status_code >= 400:
            return {"status": "failed", "error": f"http {r.status_code}"}
        total = 0
        with open(ruta, "wb") as f:
            for chunk in r.iter_bytes():
                total += len(chunk)
                if total > MAX_BYTES:
                    return {"status": "failed", "error": "archivo excede el limite"}
                f.write(chunk)
    return {"status": "ok", "ruta": str(ruta), "bytes": total}

def extraer(paquete: str, destino: str) -> dict:
    dst = Path(destino).resolve()
    dst.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(paquete):
        with zipfile.ZipFile(paquete) as z:
            for m in z.namelist():
                if not (dst / m).resolve().is_relative_to(dst):
                    return {"status": "failed", "error": "ruta insegura en zip"}
            z.extractall(dst)
        return {"status": "ok", "formato": "zip"}
    if tarfile.is_tarfile(paquete):
        with tarfile.open(paquete) as t:
            for m in t.getmembers():
                if not (dst / m.name).resolve().is_relative_to(dst) or m.issym() or m.islnk():
                    return {"status": "failed", "error": "miembro inseguro en tar"}
            t.extractall(dst, filter="data")
        return {"status": "ok", "formato": "tar"}
    return {"status": "failed", "error": "formato no reconocido"}

def fusionar(candidatos: list, criterio=lambda c: c.get("stars", 0)) -> list:
    vistos, salida = set(), []
    for c in sorted(candidatos, key=criterio, reverse=True):
        clave = c["url"].lower().rstrip("/")
        if clave not in vistos:
            vistos.add(clave)
            salida.append(c)
    return salida[:TOP_N]
