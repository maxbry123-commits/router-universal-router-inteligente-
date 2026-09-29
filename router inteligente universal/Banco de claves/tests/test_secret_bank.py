from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from secret_bank import (  # noqa: E402
    InvalidPassphrase, NotFound, PermissionDenied, SecretBroker, SessionExpired, SessionManager, Vault,
    VaultCorrupt, VaultError,
)

FAST_KDF = {"n": 2**12, "r": 8, "p": 1}  # rápido para tests; producción usa 2**15
PASS = "contraseña-maestra-de-prueba-1"
SECRET = "SECRETO-DE-PRUEBA-NO-REAL-0123456789"


class SecretBankTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "vault.db"
        self.vault = Vault(self.path, kdf=FAST_KDF)
        self.vault.initialize(PASS)
        self.unlocked = self.vault.unlock(PASS)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_wrong_passphrase_and_short_passphrase_fail(self):
        with self.assertRaises(InvalidPassphrase):
            self.vault.unlock("otra-contraseña-incorrecta")
        with self.assertRaises(VaultError):
            Vault(Path(self.tmp.name) / "v2.db", kdf=FAST_KDF).initialize("corta")
        with self.assertRaises(VaultError):
            self.vault.initialize(PASS)  # ya existe

    def test_file_never_contains_secret_or_passphrase_and_list_has_no_values(self):
        self.unlocked.put("anthropic/primary", SECRET, allowed_agents=["a1"], allowed_models=["*"], allowed_routes=["*"])
        raw = self.path.read_bytes()
        self.assertNotIn(SECRET.encode(), raw)
        self.assertNotIn(PASS.encode(), raw)
        listed = self.unlocked.list()
        self.assertEqual(listed[0]["credential_ref"], "anthropic/primary")
        self.assertNotIn(SECRET, repr(listed))
        self.assertNotIn(SECRET, repr(self.unlocked.audit_log()))
        self.assertNotIn("key", repr(self.unlocked).lower().replace("unlockedvault", ""))

    def test_same_secret_encrypts_differently_and_persists_across_reopen(self):
        self.unlocked.put("kimi/a", SECRET)
        self.unlocked.put("kimi/b", SECRET)
        conn = sqlite3.connect(self.path)
        blobs = [r[0] for r in conn.execute("SELECT ciphertext FROM credentials ORDER BY credential_ref")]
        conn.close()
        self.assertNotEqual(blobs[0], blobs[1])
        reopened = Vault(self.path, kdf=FAST_KDF).unlock(PASS)
        self.assertEqual(reopened.get_secret("kimi/a"), SECRET)

    def test_backup_copy_restores_with_passphrase(self):
        self.unlocked.put("huggingface/primary", SECRET)
        backup = Path(self.tmp.name) / "backup.db"
        backup.write_bytes(self.path.read_bytes())
        self.assertEqual(Vault(backup, kdf=FAST_KDF).unlock(PASS).get_secret("huggingface/primary"), SECRET)
        with self.assertRaises(InvalidPassphrase):
            Vault(backup, kdf=FAST_KDF).unlock("contraseña-equivocada-123")

    def test_invalid_ref_duplicate_and_empty_secret(self):
        for bad in ("sinbarra", "UPPER/case", "a/b/c", "/x", "x/"):
            with self.assertRaises(VaultError):
                self.unlocked.put(bad, SECRET)
        self.unlocked.put("groq/primary", SECRET)
        with self.assertRaises(VaultError):
            self.unlocked.put("groq/primary", SECRET)
        with self.assertRaises(VaultError):
            self.unlocked.put("groq/empty", "")

    def test_ciphertext_cannot_be_moved_between_credentials(self):
        self.unlocked.put("kimi/a", SECRET)
        self.unlocked.put("kimi/b", "OTRO-SECRETO-DE-PRUEBA-999999")
        conn = sqlite3.connect(self.path)
        a = conn.execute("SELECT nonce, ciphertext FROM credentials WHERE credential_ref='kimi/a'").fetchone()
        conn.execute("UPDATE credentials SET nonce=?, ciphertext=? WHERE credential_ref='kimi/b'", a)
        conn.commit()
        conn.close()
        with self.assertRaises(VaultCorrupt):
            self.unlocked.get_secret("kimi/b")

    def test_rotate_disable_delete_and_expiry(self):
        self.unlocked.put("minimax/primary", SECRET, expires_at=100.0)
        with self.assertRaises(PermissionDenied):
            self.unlocked.get_secret("minimax/primary", now=100.0)
        self.assertEqual(self.unlocked.get_secret("minimax/primary", now=99.0), SECRET)
        self.unlocked.rotate("minimax/primary", "NUEVO-SECRETO-DE-PRUEBA-777777")
        self.assertEqual(self.unlocked.get_secret("minimax/primary", now=99.0), "NUEVO-SECRETO-DE-PRUEBA-777777")
        self.assertIsNotNone(self.unlocked.get_record("minimax/primary")["rotated_at"])
        self.unlocked.set_enabled("minimax/primary", False)
        with self.assertRaises(PermissionDenied):
            self.unlocked.get_secret("minimax/primary", now=1.0)
        self.unlocked.delete("minimax/primary")
        with self.assertRaises(NotFound):
            self.unlocked.get_record("minimax/primary")

    def test_broker_permissions_are_fail_closed_and_audited_without_values(self):
        clock = [1000.0]
        sessions = SessionManager(ttl_seconds=60, clock=lambda: clock[0], kdf=FAST_KDF)
        sid = sessions.login(self.path, PASS)
        vault = sessions.get(sid)
        vault.put("anthropic/primary", SECRET, allowed_agents=["agent-01"], allowed_models=["claude-x"], allowed_routes=["router"])
        vault.put("cerebras/open", SECRET, allowed_agents=["*"], allowed_models=["*"], allowed_routes=["*"])
        vault.put("groq/none", SECRET)  # listas vacías = deniega
        broker = SecretBroker(sessions, clock=lambda: clock[0])
        seen = []
        out = broker.with_secret(sid, "anthropic/primary", agent="agent-01", model="claude-x", route="router",
                                 fn=lambda s: (seen.append(s), "respuesta-sin-clave")[1])
        self.assertEqual(out, "respuesta-sin-clave")
        self.assertEqual(seen, [SECRET])
        for kw in ({"agent": "agent-02", "model": "claude-x", "route": "router"},
                   {"agent": "agent-01", "model": "otro", "route": "router"},
                   {"agent": "agent-01", "model": "claude-x", "route": "externa"}):
            with self.assertRaises(PermissionDenied):
                broker.with_secret(sid, "anthropic/primary", fn=lambda s: s, **kw)
        self.assertEqual(broker.with_secret(sid, "cerebras/open", agent="x", model="y", route="z", fn=lambda s: 1), 1)
        with self.assertRaises(PermissionDenied):
            broker.with_secret(sid, "groq/none", agent="x", model="y", route="z", fn=lambda s: s)
        with self.assertRaises(NotFound):
            broker.with_secret(sid, "nadie/nada", agent="x", model="y", route="z", fn=lambda s: s)
        events = [e["event"] for e in vault.audit_log()]
        self.assertIn("USE", events)
        self.assertGreaterEqual(events.count("DENIED"), 4)
        self.assertNotIn(SECRET, repr(vault.audit_log()))

    def test_session_login_once_ttl_and_logout(self):
        clock = [0.0]
        sessions = SessionManager(ttl_seconds=10, clock=lambda: clock[0], kdf=FAST_KDF)
        with self.assertRaises(InvalidPassphrase):
            sessions.login(self.path, "contraseña-equivocada-123")
        sid = sessions.login(self.path, PASS)
        self.assertGreaterEqual(len(sid), 40)
        self.assertNotEqual(sid, sessions.login(self.path, PASS))
        clock[0] = 9.0
        sessions.get(sid)  # sigue abierta: sin pedir la contraseña otra vez
        clock[0] = 10.0
        with self.assertRaises(SessionExpired):
            sessions.get(sid)
        sid2 = sessions.login(self.path, PASS)
        sessions.logout(sid2)
        with self.assertRaises(SessionExpired):
            sessions.get(sid2)


if __name__ == "__main__":
    unittest.main()
