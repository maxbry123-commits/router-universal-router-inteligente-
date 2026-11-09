"""Vault cifrado del Secret Bank.

SQLite + AES-256-GCM por valor. La clave se deriva con scrypt de la contraseña maestra y NUNCA se
guarda: solo vive en memoria mientras la sesión está abierta. El identificador (`provider/account`)
va como dato asociado (AAD) del cifrado: un valor cifrado no se puede copiar a otra fila.
Nada de este módulo escribe valores en logs ni en la tabla de auditoría.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

SCHEMA_VERSION = 1
DEFAULT_KDF: dict[str, int] = {"n": 2**15, "r": 8, "p": 1}
MIN_PASSPHRASE_CHARS = 12
_VERIFIER = b"YAIWES-SECRET-BANK-V1"
_REF_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*/[a-z0-9][a-z0-9_.-]*$")


class VaultError(Exception):
    """Error base del banco."""


class InvalidPassphrase(VaultError):
    pass


class VaultCorrupt(VaultError):
    pass


class NotFound(VaultError):
    pass


class PermissionDenied(VaultError):
    pass


class SessionExpired(VaultError):
    pass


def _derive(passphrase: str, salt: bytes, kdf: dict[str, int]) -> bytes:
    return Scrypt(salt=salt, length=32, n=kdf["n"], r=kdf["r"], p=kdf["p"]).derive(passphrase.encode("utf-8"))


_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE credentials (
    credential_ref TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    account TEXT NOT NULL,
    nonce BLOB NOT NULL,
    ciphertext BLOB NOT NULL,
    scope TEXT NOT NULL,
    allowed_agents TEXT NOT NULL,
    allowed_models TEXT NOT NULL,
    allowed_routes TEXT NOT NULL,
    created_at REAL NOT NULL,
    rotated_at REAL,
    expires_at REAL,
    enabled INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    event TEXT NOT NULL,
    credential_ref TEXT,
    actor TEXT,
    detail TEXT
);
"""


class Vault:
    """Archivo del vault (cerrado). `initialize` lo crea; `unlock` devuelve el vault abierto."""

    def __init__(self, path: str | os.PathLike[str], *, kdf: dict[str, int] | None = None) -> None:
        self.path = Path(path)
        self._kdf_default = dict(kdf or DEFAULT_KDF)

    def exists(self) -> bool:
        return self.path.is_file() and self.path.stat().st_size > 0

    def initialize(self, passphrase: str) -> None:
        if self.exists():
            raise VaultError("VAULT_EXISTS")
        if len(passphrase) < MIN_PASSPHRASE_CHARS:
            raise VaultError("PASSPHRASE_TOO_SHORT")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        salt = os.urandom(16)
        key = _derive(passphrase, salt, self._kdf_default)
        nonce = os.urandom(12)
        verifier = nonce + AESGCM(key).encrypt(nonce, _VERIFIER, b"verifier")
        conn = sqlite3.connect(self.path)
        try:
            conn.executescript(_SCHEMA)
            conn.executemany(
                "INSERT INTO meta(key, value) VALUES (?, ?)",
                [
                    ("schema_version", str(SCHEMA_VERSION)),
                    ("salt", salt.hex()),
                    ("kdf", json.dumps(self._kdf_default)),
                    ("verifier", verifier.hex()),
                ],
            )
            conn.commit()
        finally:
            conn.close()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def unlock(self, passphrase: str) -> "UnlockedVault":
        if not self.exists():
            raise NotFound("VAULT_MISSING")
        conn = sqlite3.connect(self.path)
        try:
            meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        finally:
            conn.close()
        try:
            key = _derive(passphrase, bytes.fromhex(meta["salt"]), json.loads(meta["kdf"]))
            blob = bytes.fromhex(meta["verifier"])
            AESGCM(key).decrypt(blob[:12], blob[12:], b"verifier")
        except (InvalidTag, KeyError, ValueError):
            raise InvalidPassphrase("INVALID_PASSPHRASE") from None
        return UnlockedVault(self.path, key)


class UnlockedVault:
    """Vault abierto: la clave de descifrado vive solo en este objeto (memoria)."""

    def __init__(self, path: Path, key: bytes) -> None:
        self._path = Path(path)
        self._aead = AESGCM(key)

    def __repr__(self) -> str:  # nunca exponer la clave
        return "<UnlockedVault>"

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _check_ref(ref: str) -> tuple[str, str]:
        if not _REF_RE.match(ref):
            raise VaultError("INVALID_CREDENTIAL_REF")
        provider, account = ref.split("/", 1)
        return provider, account

    def _seal(self, ref: str, secret: str) -> tuple[bytes, bytes]:
        nonce = os.urandom(12)
        return nonce, self._aead.encrypt(nonce, secret.encode("utf-8"), ref.encode("utf-8"))

    def _open(self, ref: str, nonce: bytes, ciphertext: bytes) -> str:
        try:
            return self._aead.decrypt(nonce, ciphertext, ref.encode("utf-8")).decode("utf-8")
        except InvalidTag:
            raise VaultCorrupt("CREDENTIAL_DECRYPT_FAILED") from None

    def audit(self, event: str, ref: str | None = None, actor: str | None = None, detail: str = "") -> None:
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO audit(ts, event, credential_ref, actor, detail) VALUES (?, ?, ?, ?, ?)",
                (time.time(), event, ref, actor, detail),
            )
            conn.commit()
        finally:
            conn.close()

    def put(
        self,
        ref: str,
        secret: str,
        *,
        scope: str = "inference",
        allowed_agents: Iterable[str] = (),
        allowed_models: Iterable[str] = (),
        allowed_routes: Iterable[str] = (),
        expires_at: float | None = None,
        actor: str = "owner",
    ) -> None:
        provider, account = self._check_ref(ref)
        if not secret:
            raise VaultError("EMPTY_SECRET")
        nonce, ciphertext = self._seal(ref, secret)
        conn = self._conn()
        try:
            try:
                conn.execute(
                    "INSERT INTO credentials(credential_ref, provider, account, nonce, ciphertext, scope,"
                    " allowed_agents, allowed_models, allowed_routes, created_at, expires_at, enabled)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                    (ref, provider, account, nonce, ciphertext, scope, json.dumps(sorted(set(allowed_agents))),
                     json.dumps(sorted(set(allowed_models))), json.dumps(sorted(set(allowed_routes))),
                     time.time(), expires_at),
                )
            except sqlite3.IntegrityError:
                raise VaultError("CREDENTIAL_EXISTS") from None
            conn.commit()
        finally:
            conn.close()
        self.audit("PUT", ref, actor)

    @staticmethod
    def _public(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "credential_ref": row["credential_ref"],
            "provider": row["provider"],
            "account": row["account"],
            "scope": row["scope"],
            "allowed_agents": json.loads(row["allowed_agents"]),
            "allowed_models": json.loads(row["allowed_models"]),
            "allowed_routes": json.loads(row["allowed_routes"]),
            "created_at": row["created_at"],
            "rotated_at": row["rotated_at"],
            "expires_at": row["expires_at"],
            "enabled": bool(row["enabled"]),
        }

    def list(self) -> list[dict[str, Any]]:
        conn = self._conn()
        try:
            return [self._public(r) for r in conn.execute("SELECT * FROM credentials ORDER BY credential_ref")]
        finally:
            conn.close()

    def get_record(self, ref: str) -> dict[str, Any]:
        conn = self._conn()
        try:
            row = conn.execute("SELECT * FROM credentials WHERE credential_ref = ?", (ref,)).fetchone()
        finally:
            conn.close()
        if row is None:
            raise NotFound("CREDENTIAL_NOT_FOUND")
        return self._public(row)

    def get_secret(self, ref: str, *, now: float | None = None) -> str:
        """USO INTERNO del broker. Comprueba habilitada y caducidad antes de descifrar."""
        conn = self._conn()
        try:
            row = conn.execute("SELECT * FROM credentials WHERE credential_ref = ?", (ref,)).fetchone()
        finally:
            conn.close()
        if row is None:
            raise NotFound("CREDENTIAL_NOT_FOUND")
        if not row["enabled"]:
            raise PermissionDenied("CREDENTIAL_DISABLED")
        expires = row["expires_at"]
        if expires is not None and (time.time() if now is None else now) >= expires:
            raise PermissionDenied("CREDENTIAL_EXPIRED")
        return self._open(ref, row["nonce"], row["ciphertext"])

    def rotate(self, ref: str, new_secret: str, *, actor: str = "owner") -> None:
        self._check_ref(ref)
        if not new_secret:
            raise VaultError("EMPTY_SECRET")
        nonce, ciphertext = self._seal(ref, new_secret)
        conn = self._conn()
        try:
            cur = conn.execute(
                "UPDATE credentials SET nonce = ?, ciphertext = ?, rotated_at = ?, enabled = 1 WHERE credential_ref = ?",
                (nonce, ciphertext, time.time(), ref),
            )
            if cur.rowcount == 0:
                raise NotFound("CREDENTIAL_NOT_FOUND")
            conn.commit()
        finally:
            conn.close()
        self.audit("ROTATE", ref, actor)

    def set_enabled(self, ref: str, enabled: bool, *, actor: str = "owner") -> None:
        conn = self._conn()
        try:
            cur = conn.execute("UPDATE credentials SET enabled = ? WHERE credential_ref = ?", (1 if enabled else 0, ref))
            if cur.rowcount == 0:
                raise NotFound("CREDENTIAL_NOT_FOUND")
            conn.commit()
        finally:
            conn.close()
        self.audit("ENABLE" if enabled else "DISABLE", ref, actor)

    def delete(self, ref: str, *, actor: str = "owner") -> None:
        conn = self._conn()
        try:
            cur = conn.execute("DELETE FROM credentials WHERE credential_ref = ?", (ref,))
            if cur.rowcount == 0:
                raise NotFound("CREDENTIAL_NOT_FOUND")
            conn.commit()
        finally:
            conn.close()
        self.audit("DELETE", ref, actor)

    def audit_log(self, limit: int = 200) -> list[dict[str, Any]]:
        conn = self._conn()
        try:
            rows = conn.execute("SELECT ts, event, credential_ref, actor, detail FROM audit ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in rows]
        finally:
            conn.close()
