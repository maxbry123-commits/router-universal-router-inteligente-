"""Starts the Router (FastAPI chat + banks + policy routing) inside a Hugging Face Job: places the encrypted bank (from the repo) at RIU_VAULT_PATH and
runs uvicorn on port 8000. The bank passphrase is NOT in the Job: the Director types it in the chat's "Claves" tab (kept in memory, 1 h)."""
from __future__ import annotations

import base64
import gzip
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # router inteligente universal
MK = ROOT / "agent-microkernel"


def bank_text() -> str:
    single = MK / "runtime-bank.db.gz.b64"
    if single.exists() and single.read_text().strip().startswith("H4sI"):
        return single.read_text().strip()
    return "".join(p.read_text().strip() for p in sorted(MK.glob("runtime-bank-v2.part*")))


def main() -> None:
    vault = Path(os.environ.setdefault("RIU_VAULT_PATH", "/tmp/riu_vault.db"))
    os.environ.setdefault("RIU_DATA_DIR", "/tmp/riu")
    os.environ.setdefault("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")
    text = bank_text()
    if text:
        vault.write_bytes(gzip.decompress(base64.b64decode(text)))
        print(f"banco cifrado colocado en {vault} ({vault.stat().st_size} bytes)", flush=True)
    os.chdir(ROOT)
    os.execvp(sys.executable, [sys.executable, "-m", "uvicorn", "integration.chat_mvp.app:app", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()
