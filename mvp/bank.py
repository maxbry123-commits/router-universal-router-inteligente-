"""Banco MVPB1 cifrado con Fernet; ninguna credencial se registra en logs."""
import base64
import hashlib
import json
import os
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

MARCA = b"MVPB1"
SECRETOS = ("HF_TOKEN", "GITHUB_TOKEN", "QWEN_API_KEY")


class Banco:
    def __init__(self, ruta, clave):
        if not isinstance(clave, str) or not clave:
            raise ValueError("clave de acceso requerida")
        self._ruta = Path(ruta)
        if self._ruta.is_symlink():
            raise ValueError("ruta del banco no permitida")
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        raw = self._ruta.read_bytes() if self._ruta.exists() else None
        if raw is not None and (len(raw) < 22 or raw[:5] != MARCA):
            raise ValueError("formato del banco invalido")
        self._sal = raw[5:21] if raw is not None else os.urandom(16)
        derivada = hashlib.pbkdf2_hmac("sha256", clave.encode(), self._sal, 200000, 32)
        self._fernet = Fernet(base64.urlsafe_b64encode(derivada))
        try:
            self._datos = json.loads(self._fernet.decrypt(raw[21:])) if raw else {}
            if not isinstance(self._datos, dict):
                raise ValueError("formato invalido")
        except (InvalidToken, ValueError, UnicodeDecodeError):
            raise ValueError("clave incorrecta o banco corrupto") from None
        if raw is None:
            self._persistir()

    def _persistir(self):
        contenido = json.dumps(self._datos, ensure_ascii=False).encode("utf-8")
        bloque = MARCA + self._sal + self._fernet.encrypt(contenido)
        fd, temporal = tempfile.mkstemp(dir=self._ruta.parent, prefix=".banco-")
        try:
            with os.fdopen(fd, "wb") as archivo:
                archivo.write(bloque)
            if self._ruta.is_symlink():
                raise ValueError("ruta del banco no permitida")
            os.replace(temporal, self._ruta)
        finally:
            if os.path.exists(temporal):
                os.unlink(temporal)

    def guardar(self, nombre, valor):
        if not isinstance(nombre, str) or not nombre.isidentifier():
            raise ValueError("nombre invalido")
        if not isinstance(valor, str):
            raise ValueError("valor invalido")
        self._datos[nombre] = valor
        self._persistir()

    def leer(self, nombre):
        return self._datos.get(nombre)

    def nombres(self):
        return sorted(self._datos)

    def bootstrap_desde_env(self, mapa=None):
        mapa = mapa if mapa is not None else {nombre: nombre for nombre in SECRETOS}
        for nombre in SECRETOS:
            variable = mapa.get(nombre, nombre)
            valor = os.environ.get(variable, "") if isinstance(variable, str) else ""
            if nombre not in self._datos and valor:
                self.guardar(nombre, valor)
        return self.nombres()


def abrir(ruta, clave):
    return Banco(ruta, clave)
