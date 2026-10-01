"""Bridge between the chat and the YAIWES Secret Bank (Banco de claves/secret_bank/vault.py).

* The master passphrase is never stored: the bank is unlocked in memory for a TTL (RIU_VAULT_AUTOLOCK_S; 0 = never, the default; legacy RIU_VAULT_TTL still honoured).
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
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

from . import github_tools as gh
from . import vault_hook

# Built-in fallback (used when providers.json is missing or invalid). New providers go in providers.json, one entry each.
DEFAULT_PROVIDER_MAP = {"nvidia": "nvidia", "hf": "huggingface", "groq": "groq",
                        "deepseek": "deepseek", "moonshot": "moonshot", "minimax": "minimax",
                        "openai": "openai"}
PROVIDER_MAP = DEFAULT_PROVIDER_MAP  # backwards-compatible name; live view: provider_map()
AUTH_FORMATS = ("bearer", "x-api-key", "header", "query", "none")
# Autolock: 0 = the bank never closes by itself (Director: 24/7). Set RIU_VAULT_AUTOLOCK_S=3600 to get the old 1 h behaviour.
DEFAULT_AUTOLOCK_S = 0.0
DEFAULT_TTL = DEFAULT_AUTOLOCK_S  # legacy alias
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_PROV_CACHE: dict[str, Any] = {"sig": None, "data": None}


def providers_file() -> Path:
    env = os.getenv("RIU_VAULT_PROVIDERS_FILE")
    return Path(env) if env else Path(__file__).resolve().parent / "providers.json"


def _defaults() -> dict[str, dict[str, Any]]:
    return {k: {"vault_provider": v, "auth": "bearer"} for k, v in DEFAULT_PROVIDER_MAP.items()}


def _clean_entry(name: str, raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, str):
        raw = {"vault_provider": raw}
    if not isinstance(raw, dict) or not _NAME_RE.match(name):
        return None
    vp = raw.get("vault_provider") or name
    auth = raw.get("auth") or "bearer"
    base = raw.get("base_url")
    env = raw.get("env")
    if not (isinstance(vp, str) and _NAME_RE.match(vp)) or auth not in AUTH_FORMATS:
        return None
    if base is not None and not (isinstance(base, str) and base.startswith(("http://", "https://"))):
        return None
    if env is not None and not (isinstance(env, str) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", env)):
        return None
    out: dict[str, Any] = {"vault_provider": vp, "auth": auth}
    if base:
        out["base_url"] = base
    if env:
        out["env"] = env
    if isinstance(raw.get("auth_header"), str) and raw["auth_header"]:
        out["auth_header"] = raw["auth_header"]
    return out


def load_providers() -> dict[str, dict[str, Any]]:
    """Built-in providers + providers.json entries (JSON wins). Missing/invalid file or entry -> skipped, never raises."""
    path = providers_file()
    try:
        st = path.stat()
        sig: Any = (str(path), st.st_mtime_ns, st.st_size)
    except OSError:
        return _defaults()
    if _PROV_CACHE["sig"] == sig:
        return dict(_PROV_CACHE["data"])
    merged = _defaults()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw.get("providers", raw) if isinstance(raw, dict) else {}
        for name, entry in (entries.items() if isinstance(entries, dict) else []):
            if isinstance(name, str) and not name.startswith("_"):
                clean = _clean_entry(name, entry)
                if clean:
                    merged[name] = clean
    except (OSError, ValueError):
        merged = _defaults()
    _PROV_CACHE["sig"], _PROV_CACHE["data"] = sig, merged
    return dict(merged)


def provider_map() -> dict[str, str]:
    return {k: v["vault_provider"] for k, v in load_providers().items()}


def autolock_seconds() -> float:
    """RIU_VAULT_AUTOLOCK_S wins, then legacy RIU_VAULT_TTL, else DEFAULT_AUTOLOCK_S. 0 (or negative) = never."""
    for name in ("RIU_VAULT_AUTOLOCK_S", "RIU_VAULT_TTL"):
        raw = os.getenv(name)
        if raw not in (None, ""):
            try:
                return max(0.0, float(raw))
            except ValueError:
                continue
    return DEFAULT_AUTOLOCK_S
MAX_FAILS = 5
LOCK_SECONDS = 600.0


class BankError(RuntimeError):
    pass


def _load_vault_module() -> Any:
    here = Path(__file__).resolve()
    candidates = [here.parent / "secret_vault.py", *(p / "Banco de claves" / "secret_bank" / "vault.py" for p in here.parents)]
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
                               "ttl_seconds": (None if self._until == float("inf") else max(0, int(self._until - time.time()))) if alive else 0,
                               "autolock_s": autolock_seconds()}
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
            lock_after = autolock_seconds()
            self._until = now + lock_after if lock_after > 0 else float("inf")
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
        pmap = provider_map()
        if provider not in pmap or not self._alive():
            return []
        keys: list[str] = []
        for rec in sorted(self._open.list(), key=lambda r: r["created_at"]):
            if rec["provider"] == pmap[provider] and rec["enabled"] and rec["scope"] != "github":
                try:
                    keys.append(self._open.get_secret(rec["credential_ref"]))
                except Exception as exc:  # noqa: BLE001 - expired/disabled entries are skipped
                    logging.getLogger(__name__).debug("key skipped: %s", exc)
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
            except Exception as exc:  # noqa: BLE001
                logging.getLogger(__name__).debug("gh record skipped: %s", exc)
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
        except Exception as exc:
            raise BankError("VAULT_IMPORT_INVALID") from exc
        if not raw.startswith(b"SQLite format 3"):
            raise BankError("VAULT_IMPORT_INVALID")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return len(raw)


bridge = VaultBridge()
vault_hook.set_provider_keys(bridge.provider_keys)
