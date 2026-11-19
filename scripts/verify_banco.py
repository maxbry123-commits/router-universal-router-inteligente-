#!/usr/bin/env python3
"""verify_banco.py — Gate de seguridad del banco: ningún secreto en claro.

Comprueba que los ficheros publicados del banco NO contienen claves en claro
(nvapi-, gsk_, sk-sp-, tokens de GitHub o de HF, ni la clave maestra) y que el
`vault.json` es solo ciphertext (AES-256-GCM con scrypt).

Uso:  python3 scripts/verify_banco.py [directorio]
Salida: OK / FALLO (exit 1 si hay un secreto en claro).
"""
import json
import pathlib
import re
import sys

PATRONES = {
    "nvidia": re.compile(r"nvapi-[A-Za-z0-9_\-]{10,}"),
    "groq": re.compile(r"gsk_[A-Za-z0-9]{10,}"),
    "qwen": re.compile(r"sk-sp-[A-Za-z0-9]{10,}"),
    "github": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "huggingface": re.compile(r"\bhf_[A-Za-z0-9]{20,}"),
    "bearer": re.compile(r"[Bb]earer\s+[A-Za-z0-9\-_\.]{20,}"),
    "maestra": re.compile(r"\b\d{6}[A-Za-z]{3}\$\d+\b"),
}

CAMPOS_VAULT = {"version", "cipher", "kdf", "key_env", "salt", "nonce", "ciphertext_b64"}


def main() -> int:
    base = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "router/banco/hf")
    fallos = []
    if not base.is_dir():
        print(f"FALLO: no existe {base}")
        return 1
    ficheros = sorted(p for p in base.iterdir() if p.is_file() and p.suffix in (".json", ".md", ".txt", ".yaml"))
    if not ficheros:
        print(f"FALLO: sin ficheros que comprobar en {base}")
        return 1
    for p in ficheros:
        texto = p.read_text(encoding="utf-8", errors="replace")
        for nombre, patron in PATRONES.items():
            m = patron.search(texto)
            if m:
                fallos.append(f"{p.name}: patron '{nombre}' en {m.start()}")
        if p.name == "vault.json":
            try:
                claves = set(json.loads(texto).keys())
            except Exception as e:
                fallos.append(f"{p.name}: no es JSON valido ({e})")
                continue
            if claves != CAMPOS_VAULT:
                fallos.append(f"{p.name}: claves inesperadas {sorted(claves - CAMPOS_VAULT)}")
    if fallos:
        print("FALLO: hay material sensible en claro")
        for f in fallos:
            print("  -", f)
        return 1
    print(f"OK: {len(ficheros)} ficheros del banco sin secretos en claro ({base})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
