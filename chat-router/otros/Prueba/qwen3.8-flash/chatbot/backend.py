"""
Validación y troceado de archivos grandes sin truncado silencioso.
Python 3 estándar, sin dependencias externas.
Prototipo aislado para auditoría.
"""

import os
import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Fragmento:
    """Representa un fragmento troceado de un archivo."""
    indice: int
    inicio: int
    fin: int
    contenido: str
    tamano_bytes: int = 0
    hash_md5: str = ""

    def __post_init__(self):
        self.tamano_bytes = len(self.contenido.encode("utf-8"))
        self.hash_md5 = hashlib.md5(self.contenido.encode("utf-8")).hexdigest()

    def resumen(self) -> str:
        return f"[{self.indice}] bytes {self.inicio}-{self.fin} | {self.tamano_bytes}B | {self.hash_md5[:8]}"


class ValidadorEntradas:
    """Valida rutas de archivo y parámetros de troceado."""

    PATRON_RUTA = re.compile(r"^[a-zA-Z0-9_\-./\\]+$")
    TAMANO_MAXIMO_FRAGMENTO = 1_048_576  # 1 MB

    @classmethod
    def validar_ruta(cls, ruta: str) -> Tuple[bool, str]:
        if not ruta or not isinstance(ruta, str):
            return False, "Ruta vacía o de tipo inválido"
        if len(ruta) > 4096:
            return False, f"Ruta excede 4096 caracteres (len={len(ruta)})"
        if not cls.PATRON_RUTA.match(ruta):
            return False, f"Caracteres no permitidos en ruta: {ruta!r}"
        if "\x00" in ruta:
            return False, "Byte nulo en ruta"
        return True, ""

    @classmethod
    def validar_tamano_fragmento(cls, tamano: int) -> Tuple[bool, str]:
        if not isinstance(tamano, int) or tamano <= 0:
            return False, f"Tamaño de fragmento inválido: {tamano}"
        if tamano > cls.TAMANO_MAXIMO_FRAGMENTO:
            return False, f"Tamaño excede límite de {cls.TAMANO_MAXIMO_FRAGMENTO} bytes"
        return True, ""

    @classmethod
    def validar_solapamiento(cls, solape: int, tamano: int) -> Tuple[bool, str]:
        if solape < 0:
            return False, f"Solape negativo: {solape}"
        if solape >= tamano:
            return False, f"Solape ({solape}) >= tamaño ({tamano}): riesgo de bucle infinito"
        return True, ""


class TroceadorArchivos:
    """Trocea archivos grandes en fragmentos manejables."""

    def __init__(self, tamano_fragmento: int = 65536, solape: int = 0):
        ok, err = ValidadorEntradas.validar_tamano_fragmento(tamano_fragmento)
        if not ok:
            raise ValueError(err)
        ok, err = ValidadorEntradas.validar_solapamiento(solape, tamano_fragmento)
        if not ok:
            raise ValueError(err)
        self.tamano_fragmento = tamano_fragmento
        self.solape = solape
        self._fragmentos: List[Fragmento] = []

    def trocear_bytes(self, datos: bytes, nombre_base: str = "archivo") -> List[Fragmento]:
        self._fragmentos.clear()
        total = len(datos)
        paso = self.tamano_fragmento - self.solape
        indice = 0
        offset = 0

        while offset < total:
            fin = min(offset + self.tamano_fragmento, total)
            chunk = datos[offset:fin]
            try:
                texto = chunk.decode("utf-8", errors="replace")
            except Exception as exc:
                texto = f"<error decodificación: {exc}>"
            frag = Fragmento(
                indice=indice,
                inicio=offset,
                fin=fin,
                contenido=texto,
            )
            self._fragmentos.append(frag)
            indice += 1
            offset += paso

        return list(self._fragmentos)

    def trocear_ruta(self, ruta: str) -> List[Fragmento]:
        ok, err = ValidadorEntradas.validar_ruta(ruta)
        if not ok:
            raise ValueError(f"Ruta inválida: {err}")
        if not os.path.isfile(ruta):
            raise FileNotFoundError(f"No existe el archivo: {ruta}")
        tam_real = os.path.getsize(ruta)
        if tam_real == 0:
            return [Fragmento(indice=0, inicio=0, fin=0, contenido="")]
        with open(ruta, "rb") as f:
            datos = f.read()
        nombre = os.path.basename(ruta)
        return self.trocear_bytes(datos, nombre_base=nombre)

    @property
    def fragmentos(self) -> List[Fragmento]:
        return list(self._fragmentos)

    def reensamblear(self) -> str:
        if not self._fragmentos:
            return ""
        partes = [f.contenido for f in self._fragmentos]
        if self.solape > 0 and len(partes) > 1:
            for i in range(1, len(partes)):
                partes[i] = partes[i][self.solape:]
        return "".join(partes)

    def resumen(self) -> str:
        n = len(self._fragmentos)
        if n == 0:
            return "Sin fragmentos"
        total_bytes = sum(f.tamano_bytes for f in self._fragmentos)
        return f"{n} fragmentos, {total_bytes} bytes totales, solape={self.solape}"


class VerificadorIntegridad:
    """Comprueba que el troceado no trunca datos de forma silenciosa."""

    @staticmethod
    def verificar(datos_originales: bytes, fragmentos: List[Fragmento]) -> dict:
        resultado = {"ok": True, "errores": []}
        if not fragmentos:
            resultado["errores"].append("Lista de fragmentos vacía")
            resultado["ok"] = False
            return resultado

        reconstruido = ""
        for i, frag in enumerate(fragmentos):
            esperado_inicio = sum(len(f.contenido) for f in fragmentos[:i]) if i > 0 else 0
            if frag.contenido and len(frag.contenido) == 0 and frag.fin > frag.inicio:
                resultado["errores"].append(f"Fragmento {i}: contenido vacío pero rango [{frag.inicio}-{frag.fin}]")
                resultado["ok"] = False
            reconstruido += frag.contenido

        original_utf8 = datos_originales.decode("utf-8", errors="replace")
        if len(reconstruido) != len(original_utf8):
            resultado["errores"].append(
                f"Diferencia de longitud: reconstruido={len(reconstruido)} original={len(original_utf8)}"
            )
            resultado["ok"] = False

        return resultado


def prueba_troceado_basico():
    datos = b"ABCDEFGHIJ" * 20
    troceador = TroceadorArchivos(tamano_fragmento=32)
    frags = troceador.trocear_bytes(datos)
    assert len(frags) >= 2, f"Se esperaban al menos 2 fragmentos, se obtuvieron {len(frags)}"
    assert troceador.reensamblear().replace("\n", "") == datos.decode(), "Reensamble incorrecto"
    return "PRUEBA BÁSICA TROCEADO: OK"


def prueba_solape():
    datos = b"0123456789" * 10
    troceador = TroceadorArchivos(tamano_fragmento=16, solape=4)
    frags = troceador.trocear_bytes(datos)
    for f in frags:
        assert len(f.contenido) <= 16, f"Fragmento excede tamaño: {len(f.contenido)}"
    return "PRUEBA SOLAPE: OK"


def prueba_validacion_rutas():
    casos = [
        ("", False),
        ("../../etc/passwd", False),
        ("ruta validA.txt", False),
        ("C:\\archivos\\datos.bin", True),
        ("/tmp/archivo.txt", True),
    ]
    for ruta, esperado in casos:
        ok, _ = ValidadorEntradas.validar_ruta(ruta)
        assert ok == esperado, f"Validación incorrecta para ruta {ruta!r}: esperado={esperado} obtenido={ok}"
    return "PRUEBA VALIDACIÓN RUTAS: OK"


def prueba_hash_fragmentos():
    datos = b"hello world" * 100
    troceador = TroceadorArchivos(tamano_fragmento=48)
    frags = troceador.trocear_bytes(datos)
    hashes = [f.hash_md5 for f in frags]
    assert all(len(h) == 32 for h in hashes), "Hashes no tienen 32 caracteres hex"
    assert len(set(hashes)) == len(hashes), "Hashes duplicados inesperados"
    return "PRUEBA HASH: OK"


def ejecutar_pruebas() -> str:
    resultados = []
    pruebas = [
        prueba_validacion_rutas,
        prueba_troceado_basico,
        prueba_solape,
        prueba_hash_fragmentos,
    ]
    for prueba in pruebas:
        try:
            r = prueba()
            resultados.append(r)
        except Exception as exc:
            resultados.append(f"FALLO {prueba.__name__}: {exc}")
    return "\n".join(resultados)


if __name__ == "__main__":
    print("=== Troceador de archivos (prototipo aislado) ===")
    print(ejecutar_pruebas())
    print("=== Fin. No se inicia servidor. ===")
