# temp_cache.py
import time
import sqlite3
import json
import threading
from pathlib import Path

class TempCache:
    """
    Caché temporal con TTL.
    - Usa SQLite en /tmp (sobrevive al worker, no al restart).
    - Cada entrada expira tras `ttl_s` segundos.
    - Limpieza automática cada 60s.
    """
    def __init__(self, db_path: str = "/tmp/temp_cache.db", ttl_s: int = 3600):
        self.db_path = db_path
        self.ttl_s = ttl_s
        self.lock = threading.Lock()
        self._init_db()
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()

    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            conn.commit()
            conn.close()

    def set(self, key: str, value: dict, ttl_s: int = None):
        ttl = ttl_s or self.ttl_s
        expires = time.time() + ttl
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), expires)
            )
            conn.commit()
            conn.close()

    def get(self, key: str):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            conn.close()
        if not row:
            return None
        value, expires_at = row
        if time.time() > expires_at:
            self.delete(key)
            return None
        return json.loads(value)

    def delete(self, key: str):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            conn.close()

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
                conn.commit()
                conn.close()

    def clear(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM cache")
            conn.commit()
            conn.close()
