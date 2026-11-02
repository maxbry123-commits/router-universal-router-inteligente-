"""P0 storage contract tests. Offline/isolated; NOT a live HF/E2E test.
CIT-50/Watchdog use the existing plugins.hf_storage bucket backend.
"""
from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from plugins.hf_storage import plugin as storage


class FakeHfFiles:
    def __init__(self):
        self.files = {}
        self.corrupt_reads = False

    def pipe_file(self, uri, data):
        self.files[uri] = bytes(data)

    def cat_file(self, uri):
        if uri not in self.files:
            raise FileNotFoundError(uri)
        value = self.files[uri]
        return b"corrupted" if self.corrupt_reads else value


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "cola50.sqlite3"
        self.fs = FakeHfFiles()
        self.stub = patch.object(storage, "_fs", return_value=self.fs)
        self.stub.start()
        self.addCleanup(self.stub.stop)

    def _row(self, path):
        with sqlite3.connect(str(path)) as c:
            return c.execute("SELECT value FROM task_state").fetchone()[0]

    def test_full_roundtrip_uses_sqlite_backup_not_raw_wal(self):
        with sqlite3.connect(str(self.db)) as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("CREATE TABLE task_state(value TEXT)")
            c.execute("INSERT INTO task_state VALUES('claimed')")
        result = storage.sqlite_checkpoint(self.db, "cola50")
        self.assertTrue(result["ok"])
        uri = storage._full("tasks/system/cola50.sqlite3")
        self.assertEqual(result["sha256"], hashlib.sha256(self.fs.files[uri]).hexdigest())
        # Simulate a clean Space clone, where the SQLite WAL/shm also vanish.
        self.db.unlink()
        for suffix in ("-wal", "-shm"):
            Path(str(self.db) + suffix).unlink(missing_ok=True)
        recovered = storage.sqlite_restore_if_missing(self.db, "cola50")
        self.assertEqual(recovered["status"], "RESTORED")
        self.assertEqual(self._row(self.db), "claimed")

    def test_corrupted_snapshot_does_not_create_a_db(self):
        self.fs.files[storage._full("tasks/system/cola50.sqlite3")] = b"bad snapshot"
        with self.assertRaises((RuntimeError, sqlite3.DatabaseError)):
            storage.sqlite_restore_if_missing(self.db, "cola50")
        self.assertFalse(self.db.exists())

    def test_remote_unavailable_never_returns_new_empty_state(self):
        with patch.object(storage, "_fs", side_effect=RuntimeError("HF unavailable")):
            with self.assertRaisesRegex(RuntimeError, "HF unavailable"):
                storage.sqlite_restore_if_missing(self.db, "watchdog48")
        self.assertFalse(self.db.exists())

    def test_no_snapshot_is_explicit_first_boot(self):
        out = storage.sqlite_restore_if_missing(self.db, "cola50")
        self.assertEqual(out["status"], "FIRST_BOOT_NO_SNAPSHOT")
        self.assertFalse(self.db.exists())

    def test_readback_mismatch_prevents_durable_success(self):
        with sqlite3.connect(str(self.db)) as c:
            c.execute("CREATE TABLE task_state(value TEXT)")
            c.execute("INSERT INTO task_state VALUES('claimed')")
        self.fs.corrupt_reads = True
        with self.assertRaisesRegex(RuntimeError, "READBACK_MISMATCH"):
            storage.sqlite_checkpoint(self.db, "cola50")

    def test_whitelist_prevents_other_storage_paths(self):
        with self.assertRaises(ValueError):
            storage.sqlite_checkpoint(self.db, "malicious")
        with self.assertRaises(ValueError):
            storage.sqlite_restore_if_missing(self.db, "other")

if __name__ == "__main__":
    unittest.main()
