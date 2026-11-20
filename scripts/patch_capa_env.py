"""Append /capa/env a capa_api.py. Idempotente.
Fail-soft: si capa_api.py no existe, avisa y no hace nada (no aborta)."""
import os
import sys

TARGET = "external/api/capa_api.py"

BLOCK = '''

@app.get("/capa/env")
async def env_summary(x_api_key: str = Header(None)):
    _check(x_api_key)
    from external.core.env_config import get_env
    cfg = get_env()
    return {"masked": cfg.masked_summary(), "missing_required": cfg.validate_required()}
'''


def main():
    if not os.path.exists(TARGET):
        print(f"SKIP: {TARGET} no existe (capa_api no creada aún).")
        return
    with open(TARGET, "r", encoding="utf-8") as f:
        src = f.read()
    if "/capa/env" in src:
        print("IDEMPOTENTE: /capa/env ya presente.")
        return
    with open(TARGET, "a", encoding="utf-8") as f:
        f.write(BLOCK)
    print(f"OK: /capa/env añadido a {TARGET}")


if __name__ == "__main__":
    main()
