"""Cifra / abre archivos de fichas con la clave del banco. La clave SOLO se lee de la variable FICHA_CLAVE_BANCO, nunca se escribe en disco.
Uso: python -m motor.sellar sellar ruta [ruta...]   -> crea ruta.sello y borra el original
     python -m motor.sellar abrir ruta.sello        -> imprime el contenido (no lo guarda)"""
import hashlib
import os
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CAB = b'FICHA-SELLO-1'


def llave(sal):
    clave = os.environ.get('FICHA_CLAVE_BANCO', '')
    if not clave:
        raise SystemExit('falta FICHA_CLAVE_BANCO en el entorno')
    return hashlib.scrypt(clave.encode(), salt=sal, n=2 ** 15, r=8, p=1, dklen=32, maxmem=2 ** 26)


def sellar_bytes(datos):
    sal, nonce = os.urandom(16), os.urandom(12)
    return CAB + sal + nonce + AESGCM(llave(sal)).encrypt(nonce, datos, CAB)


def abrir_bytes(blob):
    if not blob.startswith(CAB):
        raise ValueError('no es un sello')
    k = len(CAB)
    sal, nonce, cifrado = blob[k:k + 16], blob[k + 16:k + 28], blob[k + 28:]
    return AESGCM(llave(sal)).decrypt(nonce, cifrado, CAB)


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'sellar':
        for ruta in a[1:]:
            with open(ruta, 'rb') as f:
                blob = sellar_bytes(f.read())
            with open(ruta + '.sello', 'wb') as f:
                f.write(blob)
            os.remove(ruta)
            print('sellado', ruta + '.sello')
    elif len(a) == 2 and a[0] == 'abrir':
        sys.stdout.buffer.write(abrir_bytes(open(a[1], 'rb').read()))
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
