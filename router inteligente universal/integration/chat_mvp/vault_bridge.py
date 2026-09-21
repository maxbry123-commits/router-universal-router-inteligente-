"""Bridge between the chat and the YAIWES Secret Bank (Chat Mvp/secret_bank/vault.py).

* The master passphrase is never stored: the bank is unlocked in memory for a TTL (RIU_VAULT_TTL, default 1 h).
* While unlocked, provider keys (nvidia/*, huggingface/*, ...) join the key pool via vault_hook (oldest credential first),
  and GitHub tokens (github/*) are exported as in-process env vars so the existing account selector sees them. Locking removes both.
* Values are never returned by any method that leaves this module: only credential refs (names) are listed.
* 5 wrong passphrases lock unlock attempts for 10 minutes.
"""
from __future__ import annotations

import base64
import gzip
import importlib.util
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

from . import github_tools as gh
from . import vault_hook

PROVIDER_MAP = {"nvidia": "nvidia", "hf": "huggingface", "cerebras": "cerebras", "groq": "groq",
                "deepseek": "deepseek", "moonshot": "moonshot", "minimax": "minimax"}
DEFAULT_TTL = 3600.0
MAX_FAILS = 5
LOCK_SECONDS = 600.0


class BankError(RuntimeError):
    pass


def _load_vault_module() -> Any:
    here = Path(__file__).resolve()
    candidates = [here.parent / "secret_vault.py", *(p / "Chat Mvp" / "secret_bank" / "vault.py" for p in here.parents)]
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location("riu_secret_vault", path)
            module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            return module
    raise BankError("SECRET_BANK_MODULE_NOT_FOUND")


class VaultBridge:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._open: Any = None
        self._until = 0.0
        self._fails: list[float] = []
        self._mod: Any = None
        self._exported: dict[str, str] = {}
        self._orig_accounts: str | None = None

    # -- location / module ------------------------------------------------------------
    def path(self) -> Path:
        env = os.getenv("RIU_VAULT_PATH")
        if env:
            return Path(env)
        base = Path("/data") if os.access("/data", os.W_OK) else Path.cwd() / "riu_data"
        return base / "riu_vault.db"

    def mod(self) -> Any:
        if self._mod is None:
            self._mod = _load_vault_module()
        return self._mod

    # -- state ---------------------------------------------------------------------------
    def _alive(self) -> bool:
        with self._lock:
            if self._open is not None and time.time() >= self._until:
                self.lock()
            return self._open is not None

    def status(self) -> dict[str, Any]:
        alive = self._alive()
        out: dict[str, Any] = {"exists": self.path().is_file(), "unlocked": alive,
                               "ttl_seconds": max(0, int(self._until - time.time())) if alive else 0}
        if alive:
            out["credentials"] = [{k: r[k] for k in ("credential_ref", "provider", "account", "scope", "enabled")} for r in self._open.list()]
        return out

    def unlock(self, passphrase: str) -> int:
        with self._lock:
            now = time.time()
            self._fails = [t for t in self._fails if now - t < LOCK_SECONDS]
            if len(self._fails) >= MAX_FAILS:
                raise BankError("TOO_MANY_ATTEMPTS")
            vault = self.mod().Vault(self.path())
            if not vault.exists():
                raise BankError("VAULT_MISSING")
            try:
                opened = vault.unlock(passphrase)
            except self.mod().InvalidPassphrase:
                self._fails.append(now)
                raise BankError("INVALID_PASSPHRASE") from None
            self._open = opened
            self._until = now + float(os.getenv("RIU_VAULT_TTL") or DEFAULT_TTL)
            vault_hook.set_provider_keys(self.provider_keys)
            self._export_github()
            return len(opened.list())

    def lock(self) -> None:
        with self._lock:
            self._open = None
            self._until = 0.0
            self._unexport_github()

    # -- reads used by the chat ---------------------------------------------------------
    def provider_keys(self, provider: str) -> list[str]:
        if provider not in PROVIDER_MAP or not self._alive():
            return []
        keys: list[str] = []
        for rec in sorted(self._open.list(), key=lambda r: r["created_at"]):
            if rec["provider"] == PROVIDER_MAP[provider] and rec["enabled"] and rec["scope"] != "github":
                try:
                    keys.append(self._open.get_secret(rec["credential_ref"]))
                except Exception:  # noqa: BLE001 - expired/disabled entries are skipped
                    continue
        return keys

    def _export_github(self) -> None:
        self._unexport_github()
        base = dict(gh.accounts_from_env())
        self._orig_accounts = os.environ.get("RIU_GITHUB_ACCOUNTS")
        for rec in self._open.list():
            if rec["provider"] != "github" or not rec["enabled"]:
                continue
            try:
                token = self._open.get_secret(rec["credential_ref"])
            except Exception:  # noqa: BLE001
                continue
            var = "RIU_VAULT_GH_" + re.sub(r"[^A-Z0-9]", "_", rec["account"].upper())
            os.environ[var] = token
            self._exported[var] = rec["account"]
            base[rec["account"]] = var
        if self._exported:
            os.environ["RIU_GITHUB_ACCOUNTS"] = json.dumps(base)

    def _unexport_github(self) -> None:
        for var in list(self._exported):
            os.environ.pop(var, None)
        if self._exported:
            if self._orig_accounts is None:
                os.environ.pop("RIU_GITHUB_ACCOUNTS", None)
            else:
                os.environ["RIU_GITHUB_ACCOUNTS"] = self._orig_accounts
        self._exported.clear()

    # -- writes (need the unlocked bank) --------------------------------------------------
    def _need_open(self) -> Any:
        if not self._alive():
            raise BankError("VAULT_LOCKED")
        return self._open

    def put(self, ref: str, secret: str, scope: str = "inference") -> None:
        self._need_open().put(ref, secret, scope=scope, actor="chat")
        if scope == "github":
            self._export_github()

    def rotate(self, ref: str, secret: str) -> None:
        self._need_open().rotate(ref, secret, actor="chat")
        self._export_github()

    def import_b64gz(self, b64: str) -> int:
        """Bootstrap a new host with an already-encrypted vault file (safe: it is ciphertext)."""
        path = self.path()
        if path.is_file() and path.stat().st_size > 0:
            raise BankError("VAULT_EXISTS")
        try:
            raw = gzip.decompress(base64.b64decode(b64, validate=True))
        except Exception as exc:  # noqa: BLE001
            raise BankError("VAULT_IMPORT_INVALID") from exc
        if not raw.startswith(b"SQLite format 3"):
            raise BankError("VAULT_IMPORT_INVALID")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return len(raw)


bridge = VaultBridge()
vault_hook.set_provider_keys(bridge.provider_keys)
