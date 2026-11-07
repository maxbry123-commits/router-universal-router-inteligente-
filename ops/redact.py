"""ops/redact.py — redactor de secretos para la salida de los jobs (D-118).

POR QUÉ EXISTE (veto B1 del SHERIFF, reproducido dos veces):
el patrón `... | sed "s/$GH_TOKEN/***/g"` EXPANDE el token dentro del argv del proceso
shell, así que la clave queda visible en la tabla de procesos (`ps -eo args`). Este
redactor lee el secreto del ENTORNO y sustituye su valor por `***` sin que el secreto
vaya nunca en la línea de órdenes.

USO (en cualquier job, local o contenedor):
    ... 2>&1 | python ops/redact.py | tail -40

También sirve como filtro de un fichero:
    python ops/redact.py < log.txt

No imprime NUNCA el valor del secreto, ni lo escribe en disco.
"""
import os
import re
import sys

PLACEHOLDER = "***"


def _secret_values():
    """Valores sensibles tomados del entorno (nunca de los argumentos)."""
    out = []
    for name in ("GH_TOKEN", "HF_TOKEN", "HF_TOKEN_1_NEW", "UNIVERSAL_KEY",
                 "HF_MCP_CLAUDE_PERMANENT", "GITHUB_TOKEN", "RIU_VAULT_PASSPHRASE",
                 "RIU_BANK_MASTER", "RIU_MCP_KEY", "RIU_PUBLIC_CHAT_KEY",
                 "QWEN_API_KEY", "WEB_PASS", "WEB_ACCOUNTS", "PUENTE_TOKEN"):
        v = os.environ.get(name)
        if v and len(v) >= 8:
            out.append(v)
    return out


def redact(text: str) -> str:
    for v in _secret_values():
        text = text.replace(v, PLACEHOLDER)
    # Patrones genéricos por si aparece un token con otra forma
    text = re.sub(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}", PLACEHOLDER, text)
    text = re.sub(r"\bhf_[A-Za-z0-9]{25,}", PLACEHOLDER, text)
    text = re.sub(r"(?i)(authorization:\s*basic\s+)[A-Za-z0-9+/=]{16,}", r"\1" + PLACEHOLDER, text)
    text = re.sub(r"(?i)((?:token|secret|password|api[_-]?key)\s*[:=]\s*)\S+", r"\1" + PLACEHOLDER, text)
    return text


def main():
    data = sys.stdin.buffer.read().decode("utf-8", "ignore") if not sys.stdin.isatty() else ""
    if not data:
        try:
            data = open(sys.argv[1], "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            data = ""
    sys.stdout.write(redact(data))


if __name__ == "__main__":
    main()
