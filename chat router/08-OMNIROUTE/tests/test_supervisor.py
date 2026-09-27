"""T03 — Tests del supervisor y del mantenimiento de la DB (pytest, stdlib)."""
import os
import socket
import sqlite3
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import mantenimiento_db
import supervisor_omniroute as sup


# --- backoff crece y tiene tope ---
def test_backoff_crece():
    d0 = sup.backoff_delay(0)
    d1 = sup.backoff_delay(1)
    d2 = sup.backoff_delay(2)
    assert d0 == 5
    assert d1 == 15
    assert d2 == 45
    assert d0 < d1 < d2


def test_backoff_tope():
    assert sup.backoff_delay(100) == sup.BACKOFF_MAX


# --- espera de puerto ---
def test_wait_port_free_puerto_libre():
    assert sup.wait_port_free("127.0.0.1", 0, timeout=2) is True


def test_wait_port_free_espera_y_timeout():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        assert sup.port_free("127.0.0.1", port) is False
        t0 = time.time()
        ok = sup.wait_port_free("127.0.0.1", port, timeout=2)
        assert ok is False
        assert time.time() - t0 >= 2
    finally:
        s.close()
    assert sup.port_free("127.0.0.1", port) is True


# --- lock de instancia única ---
def test_lock_impide_segunda_instancia(tmp_path):
    lock = str(tmp_path / "sup.lock")
    fd = sup.acquire_lock(lock)
    with pytest.raises(SystemExit):
        sup.acquire_lock(lock)
    os.close(fd)


def test_lock_contiene_pid(tmp_path):
    lock = str(tmp_path / "sup.lock")
    fd = sup.acquire_lock(lock)
    with open(lock) as f:
        assert f.read().strip() == str(os.getpid())
    os.close(fd)


# --- mantenimiento sobre DB temporal ---
def _mk_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE usage_history (id INTEGER PRIMARY KEY, created_at INTEGER)")
    conn.execute("CREATE TABLE call_logs (id INTEGER PRIMARY KEY, created_at TEXT)")
    conn.execute("CREATE TABLE proxy_logs (id INTEGER PRIMARY KEY, created_at INTEGER)")
    old_s = int(time.time() - 30 * 24 * 3600)          # 30 días (epoch s)
    new_ms = int(time.time() * 1000)                    # ahora (epoch ms)
    old_iso = "2020-01-01T00:00:00Z"
    new_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    conn.execute("INSERT INTO usage_history (created_at) VALUES (?)", (old_s,))
    conn.execute("INSERT INTO usage_history (created_at) VALUES (?)", (new_ms,))
    conn.execute("INSERT INTO call_logs (created_at) VALUES (?)", (old_iso,))
    conn.execute("INSERT INTO call_logs (created_at) VALUES (?)", (new_iso,))
    conn.execute("INSERT INTO proxy_logs (created_at) VALUES (?)", (old_s,))
    conn.commit()
    conn.close()


def test_mantenimiento_db_inexistente(tmp_path):
    r = mantenimiento_db.mantener(str(tmp_path / "no.sqlite"))
    assert r["existed"] is False
    assert r["deleted"] == 0


def test_mantenimiento_borra_viejo_y_conserva_nuevo(tmp_path):
    db = str(tmp_path / "storage.sqlite")
    _mk_db(db)
    r = mantenimiento_db.mantener(db)
    assert r["existed"] is True
    assert r["vacuum"] is True
    assert r["deleted"] >= 3  # 1 viejo por cada tabla
    # mmap_size es por conexión: se verifica dentro de la conexión de mantener()
    # y se devuelve en el resultado.
    assert r["mmap_size"] == 134217728
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM usage_history").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM call_logs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM proxy_logs").fetchone()[0] == 0
    finally:
        conn.close()
