"""Router <-> HF bucket bridge: sync then restore must give back the same data (fake fs, no network)."""
from __future__ import annotations

import sqlite3

from integration.chat_mvp.router import restore_from_bucket, sync_to_bucket
from integration.chat_mvp.store import Store


class FakeFS:
    files: dict[str, bytes] = {}

    def __init__(self, token: str = "") -> None:
        pass

    def pipe_file(self, path: str, data: bytes) -> None:
        FakeFS.files[path] = data

    def exists(self, path: str) -> bool:
        return path in FakeFS.files or any(p.startswith(path + "/") for p in FakeFS.files)

    def cat_file(self, path: str) -> bytes:
        return FakeFS.files[path]

    def ls(self, path: str, detail: bool = False) -> list[str]:
        return [p for p in FakeFS.files if p.startswith(path + "/")]


def test_sync_then_restore_roundtrip(tmp_path):
    FakeFS.files = {}
    store = Store(tmp_path / "a")
    store._exec("CREATE TABLE IF NOT EXISTS t(v TEXT)")
    store._exec("INSERT INTO t(v) VALUES('permanente')")
    assert sync_to_bucket(store, "org/b", "tok", fs_factory=FakeFS)["files"] >= 1
    out = restore_from_bucket(tmp_path / "b", "org/b", "tok", fs_factory=FakeFS)
    assert out["restored"] >= 1
    row = sqlite3.connect(tmp_path / "b" / "riu_chat.sqlite3").execute("SELECT v FROM t").fetchone()
    assert row == ("permanente",)


def test_restore_empty_bucket_is_noop(tmp_path):
    FakeFS.files = {}
    assert restore_from_bucket(tmp_path / "c", "org/b", "tok", fs_factory=FakeFS) == {"bucket": "org/b", "restored": 0}
