#!/usr/bin/env python3
"""T03 — Mantenimiento de la DB SQLite de OmniRoute (stdlib sqlite3).

- PRAGMA mmap_size=134217728 (128 MB).
- Retención: borra filas de usage_history / call_logs / proxy_logs con > 7 días.
- VACUUM periódico.
- Seguro si la DB no existe (sale 0 sin hacer nada).
Uso: python3 mantenimiento_db.py [ruta_db]

Nota: mmap_size es un PRAGMA POR CONEXIÓN (no se persiste en el archivo).
Por eso `mantener()` lo verifica dentro de su propia conexión y lo devuelve
en el dict resultado como "mmap_size".
"""
import os
import sqlite3
import sys
import time

DATA_DIR = os.environ.get("DATA_DIR", "/tmp/omniroute-data")
DB_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA_DIR, "storage.sqlite")
RETENTION_SECONDS = 7 * 24 * 3600
MMAP_SIZE = 134217728
TABLES = ("usage_history", "call_logs", "proxy_logs")
# Columnas de fecha candidatas (la primera que exista en la tabla se usa).
DATE_COLS = ("created_at", "timestamp", "createdAt", "ts")


def _cutoff_variants():
    """Epoch de corte en segundos y milisegundos (por si la columna es numérica)."""
    now = time.time()
    return now - RETENTION_SECONDS, (now - RETENTION_SECONDS) * 1000


def _columns(conn, table):
    try:
        return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    except sqlite3.Error:
        return []


def mantener(db_path=DB_PATH):
    if not os.path.exists(db_path):
        print(f"OK: {db_path} no existe; nada que hacer")
        return {"db": db_path, "existed": False, "deleted": 0,
                "vacuum": False, "mmap_size": 0}

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(f"PRAGMA mmap_size={MMAP_SIZE}")
        # Leer de vuelta EN ESTA conexión (el pragma es por conexión).
        mmap_actual = conn.execute("PRAGMA mmap_size").fetchone()[0]
        conn.execute("PRAGMA journal_mode=WAL")
        cut_s, cut_ms = _cutoff_variants()
        deleted = 0
        for table in TABLES:
            cols = _columns(conn, table)
            if not cols:
                continue
            date_col = next((c for c in DATE_COLS if c in cols), None)
            if date_col is None:
                continue
            # Distingue epoch-segundos de epoch-milisegundos.
            # Umbral 1e11: fechas Unix en segundos están ~1e9; en ms ~1e12.
            iso_cut = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(cut_s))
            cur = conn.execute(
                f"DELETE FROM {table} WHERE "
                f"(typeof({date_col}) IN ('integer','real') AND {date_col} > 0 "
                f" AND {date_col} < 100000000000 AND {date_col} < ?) OR "
                f"(typeof({date_col}) IN ('integer','real') AND {date_col} >= 100000000000 "
                f" AND {date_col} < ?) OR "
                f"(typeof({date_col}) = 'text' AND {date_col} < ?)",
                (cut_s, cut_ms, iso_cut),
            )
            deleted += max(cur.rowcount, 0)
        conn.commit()
        conn.execute("VACUUM")
        print(f"OK: {db_path} — borradas {deleted} filas, VACUUM hecho, "
              f"mmap_size={mmap_actual}")
        return {"db": db_path, "existed": True, "deleted": deleted,
                "vacuum": True, "mmap_size": mmap_actual}
    finally:
        conn.close()


if __name__ == "__main__":
    mantener()
