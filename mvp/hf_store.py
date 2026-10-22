"""Datos de chat en dataset HF; GitHub sigue siendo la unica fuente de codigo."""
import json
import re
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download

CONFIG = json.loads(Path(__file__).with_name("config.json").read_text(encoding="utf-8"))
PROHIBIDAS = (".py", ".pyc", ".js", ".ts", ".sh", ".env", ".pem", ".key", ".p12")
PATRON_CLAVE = re.compile(r"(?:sk-(?:sp-)?[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|hf_[A-Za-z0-9]{20,})")


def _ruta(identificador):
    if not isinstance(identificador, str) or not (1 <= len(identificador) <= 128):
        raise ValueError("ID HF invalido")
    partes = identificador.split("/")
    if (identificador.startswith("/") or "\\" in identificador or ":" in identificador
            or any(p in ("", ".", "..") or p.startswith(".") for p in partes)
            or Path(identificador).suffix.lower() in PROHIBIDAS):
        raise ValueError("ID HF no permitido")
    return CONFIG["prefijo"] + identificador


def _token(clave):
    if not isinstance(clave, str) or not clave:
        raise RuntimeError("HF_TOKEN ausente en banco")
    return clave


def guardar(clave, nombre, valor):
    ruta = _ruta(nombre)
    token = _token(clave)
    if not isinstance(valor, str) or len(valor.encode("utf-8")) > 1_000_000:
        raise ValueError("dato HF invalido")
    if PATRON_CLAVE.search(valor):
        raise ValueError("dato HF parece contener credenciales")
    try:
        info = HfApi().upload_file(path_or_fileobj=valor.encode("utf-8"),
                                   path_in_repo=ruta, repo_id=CONFIG["bucket_hf"],
                                   repo_type="dataset", token=token)
    except Exception:
        raise RuntimeError("fallo de escritura HF") from None
    return {"ok": True, "destino": "hf", "id": nombre, "commit": getattr(info, "oid", None)}


def leer(clave, nombre):
    ruta = _ruta(nombre)
    token = _token(clave)
    try:
        ruta_local = hf_hub_download(repo_id=CONFIG["bucket_hf"], filename=ruta,
                                     repo_type="dataset", token=token)
        valor = Path(ruta_local).read_text(encoding="utf-8")
    except Exception:
        raise RuntimeError("fallo de lectura HF") from None
    return {"ok": True, "destino": "hf", "id": nombre, "valor": valor}
