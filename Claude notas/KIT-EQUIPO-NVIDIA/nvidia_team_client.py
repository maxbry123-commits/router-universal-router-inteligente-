"""Cliente NVIDIA para el equipo (stdlib + `cryptography` para abrir el banco).

Uso:
  pip install cryptography
  curl -O "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/Chat%20Mvp/secret_bank/vault.py"
  export RIU_TEAM_BANK_PASSPHRASE='<la contraseña que te dio el Director>'
  python nvidia_team_client.py --bank banco-nvidia-equipo.b64 --model nvidia/nemotron-3-super-120b-a12b "Responde OK"

Las claves viven cifradas en el banco; se descifran solo en memoria. Con 4 claves hay respaldo: si una tarda o falla
(timeout, 401/402/403/429, 5xx) se usa la siguiente. Errores de petición (400/404/410/422) NO cambian de clave.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import importlib.util
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

BASE = "https://integrate.api.nvidia.com/v1"
NO_FAILOVER = {400, 404, 410, 422}


def _vault_module(path: str | None = None) -> Any:
    candidates = [Path(path)] if path else [Path(__file__).with_name("vault.py"), Path("vault.py")]
    for c in candidates:
        if c.is_file():
            spec = importlib.util.spec_from_file_location("riu_vault", c)
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod
    raise SystemExit("Falta vault.py (ver instrucciones al inicio del archivo)")


def open_bank(bank: str, passphrase: str, vault_py: str | None = None) -> list[str]:
    """`bank` = archivo .db o archivo de texto base64+gzip. Devuelve las claves NVIDIA (solo en memoria)."""
    mod = _vault_module(vault_py)
    raw = Path(bank).read_bytes()
    if not raw.startswith(b"SQLite format 3"):
        raw = gzip.decompress(base64.b64decode(raw.strip()))
    tmp = Path(tempfile.mkdtemp()) / "bank.db"
    tmp.write_bytes(raw)
    opened = mod.Vault(tmp).unlock(passphrase)
    return [opened.get_secret(r["credential_ref"]) for r in opened.list() if r["provider"] == "nvidia" and r["enabled"]]


def _post(url: str, key: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "riu-team"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read().decode())


class NvidiaPool:
    def __init__(self, keys: list[str], post: Callable[..., dict[str, Any]] = _post) -> None:
        if not keys:
            raise SystemExit("El banco no tiene claves NVIDIA")
        self.keys, self._post = keys, post

    def chat(self, model: str, messages: list[dict[str, str]], max_tokens: int = 512, timeout: float = 60.0) -> str:
        last: Exception | None = None
        for i, key in enumerate(list(self.keys)):
            try:
                data = self._post(BASE + "/chat/completions", key, {"model": model, "messages": messages, "max_tokens": max_tokens}, timeout)
                self.keys.insert(0, self.keys.pop(i))  # la clave que funcionó pasa al frente
                return ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code in NO_FAILOVER:
                    raise
            except Exception as exc:  # noqa: BLE001 - timeout / red: probar la siguiente clave
                last = exc
        raise RuntimeError(f"Ninguna de las {len(self.keys)} claves respondió: {type(last).__name__}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--bank", required=True)
    ap.add_argument("--model", default="nvidia/nemotron-3-super-120b-a12b")
    ap.add_argument("--vault-py")
    args = ap.parse_args()
    pool = NvidiaPool(open_bank(args.bank, os.environ["RIU_TEAM_BANK_PASSPHRASE"], args.vault_py))
    print(pool.chat(args.model, [{"role": "user", "content": args.prompt}]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
