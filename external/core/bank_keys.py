"""bank_keys.py — Hidrata las claves de proveedores desde el sello cifrado del repo.

Por que existe: desde el parche del banco (v10) las claves de proveedores ya NO
estan en los Secrets de HF Spaces, viven cifradas en `banco/vault.json` del bucket.
Pero el Space del proxy ya tiene `HF_VAULT_KEY` (= FICHA_CLAVE_BANCO = clave maestra)
y clona ESTE MISMO repo al arrancar, asi que el sello
`fichas/fichas_qwen/sellos/proveedores.sello` viaja con el codigo: no hace falta
ningun token de HF ni leer el bucket.

Formato del sello: `FICHA-SELLO-1` + salt(16) + nonce(12) + ciphertext AES-256-GCM,
clave derivada con scrypt(n=2^15, r=8, p=1, dklen=32) y AAD = `FICHA-SELLO-1`.

FALLO ABIERTO: si el sello no esta clonado, si falta la clave, si falta
`cryptography` o si algo falla, NO se rompe el arranque. El proxy sigue con 0
claves y lo dice en su diag (`sin claves en NVIDIA_KEYS`), igual que hoy.

Nunca se escriben claves en disco ni en logs: solo se cuentan.
"""
import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)

SELLO_REL = ("fichas", "fichas_qwen", "sellos", "proveedores.sello")
CABECERA = b"FICHA-SELLO-1"


def repo_root() -> str:
    """Raiz del repo a partir de este modulo (external/core -> ../../)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))


def sello_path() -> str:
    return os.path.join(repo_root(), *SELLO_REL)


def descifrar(blob: bytes, clave: str) -> dict:
    """Abre el sello y devuelve el JSON de proveedores."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    k = len(CABECERA)
    llave = hashlib.scrypt(
        clave.encode(), salt=blob[k:k + 16], n=2 ** 15, r=8, p=1, dklen=32, maxmem=2 ** 26
    )
    return json.loads(AESGCM(llave).decrypt(blob[k + 16:k + 28], blob[k + 28:], CABECERA).decode("utf-8"))


def hydrate(force: bool = False) -> dict:
    """Pone NVIDIA_KEYS / GROQ_KEYS / QWEN_API_KEY en el entorno si estaban vacias.

    Devuelve un recuento (nunca valores). Nunca lanza.
    """
    resumen = {"nvidia": 0, "groq": 0, "qwen": 0, "origen": "sin cambios"}
    try:
        if not force and os.getenv("NVIDIA_KEYS") and os.getenv("GROQ_KEYS"):
            resumen["origen"] = "ya estaban en el entorno"
            return resumen
        clave = os.getenv("HF_VAULT_KEY") or os.getenv("FICHA_CLAVE_BANCO") or ""
        if not clave:
            resumen["origen"] = "sin HF_VAULT_KEY"
            return resumen
        path = sello_path()
        if not os.path.isfile(path):
            resumen["origen"] = "sello no clonado"
            return resumen
        with open(path, "rb") as fh:
            blob = fh.read()
        if not blob.startswith(CABECERA):
            resumen["origen"] = "cabecera del sello no valida"
            return resumen
        data = descifrar(blob, clave)
        nvidia = [k for k in data.get("nvidia", []) if k]
        groq = [k for k in data.get("groq", []) if k]
        qwen = [k for k in data.get("qwen", []) if k]
        if nvidia and not os.getenv("NVIDIA_KEYS"):
            os.environ["NVIDIA_KEYS"] = ",".join(nvidia)
        if groq and not os.getenv("GROQ_KEYS"):
            os.environ["GROQ_KEYS"] = ",".join(groq)
        if qwen and not os.getenv("QWEN_API_KEY"):
            os.environ["QWEN_API_KEY"] = qwen[0]
        resumen = {"nvidia": len(nvidia), "groq": len(groq), "qwen": len(qwen),
                   "origen": "sello del repo"}
        logger.info("[banco] claves hidratadas desde el sello: nvidia=%d groq=%d qwen=%d",
                    len(nvidia), len(groq), len(qwen))
    except Exception as e:
        resumen["origen"] = "fallo abierto: {}: {}".format(type(e).__name__, e)
        logger.warning("[banco] no se pudieron hidratar las claves: %s", e)
    return resumen
