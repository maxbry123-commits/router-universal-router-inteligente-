from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp.storage_runtime import restore_from_bucket


class FakeFS:
    def __init__(self, token: str) -> None:
        self.token = token
        self.files = {
            "buckets/ns/bucket/riu-chat/riu_chat.sqlite3": b"sqlite-snapshot",
            "buckets/ns/bucket/riu-chat/docs/abc123": b"document-bytes",
        }

    def cat_file(self, path: str) -> bytes:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def glob(self, pattern: str) -> list[str]:
        prefix = pattern[:-1]
        return [path for path in self.files if path.startswith(prefix)]


def test_restore_from_bucket_restores_db_and_documents(tmp_path: Path) -> None:
    result = restore_from_bucket(tmp_path, "ns/bucket", "token", fs_factory=FakeFS)
    assert result["status"] == "RESTORED"
    assert result["files"] == 2
    assert (tmp_path / "riu_chat.sqlite3").read_bytes() == b"sqlite-snapshot"
    assert (tmp_path / "docs" / "abc123").read_bytes() == b"document-bytes"


def test_restore_never_overwrites_existing_local_db(tmp_path: Path) -> None:
    db = tmp_path / "riu_chat.sqlite3"
    db.write_bytes(b"local-live-db")
    result = restore_from_bucket(tmp_path, "ns/bucket", "token", fs_factory=FakeFS)
    assert result["status"] == "LOCAL_PRESENT"
    assert db.read_bytes() == b"local-live-db"
