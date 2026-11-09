"""Deterministic contract tests for ConectorDB v6 without remote DB access."""
from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "red" / "conectores.py"
spec = importlib.util.spec_from_file_location("riu_conectores_db", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules["riu_conectores_db"] = module
spec.loader.exec_module(module)
ConectorDB = module.ConectorDB


def test_conector_db_query_postgres_contract() -> None:
    connector = ConectorDB("db-test", "TEST_DB_DSN", "postgres")
    calls: list[tuple[str, str, list]] = []

    async def fake_postgres(accion: str, sql: str, params: list) -> object:
        calls.append((accion, sql, params))
        return [{"value": 1}]

    connector._postgres = fake_postgres
    result = asyncio.run(connector.enviar({
        "_accion": "query", "sql": "SELECT $1::int AS value", "params": [1]
    }))
    assert result == {"status": "DONE", "output": [{"value": 1}]}
    assert calls == [("query", "SELECT $1::int AS value", [1])]


def test_conector_db_fails_closed_for_unknown_motor_and_bad_params() -> None:
    unknown = ConectorDB("db-x", "TEST_DB_DSN", "mongo")
    result = asyncio.run(unknown.enviar({"_accion": "query", "params": []}))
    assert result == {"status": "FAIL", "error": "motor_no_soportado:mongo"}

    postgres = ConectorDB("db-p", "TEST_DB_DSN", "postgres")
    result = asyncio.run(postgres.enviar({"_accion": "query", "params": "bad"}))
    assert result == {"status": "FAIL", "error": "params_debe_ser_lista"}


def test_conector_db_secret_only_from_env_and_mysql_dsn_parser() -> None:
    connector = ConectorDB("db-test", "TEST_DB_DSN", "postgres")
    os.environ.pop("TEST_DB_DSN", None)
    try:
        connector._dsn()
        raise AssertionError("missing DSN must fail closed")
    except RuntimeError as exc:
        assert str(exc) == "env_faltante:TEST_DB_DSN"

    cfg = ConectorDB._mysql_config("mysql://user:p%40ss@db.example:3307/app")
    assert cfg == {
        "host": "db.example", "port": 3307, "user": "user",
        "password": "p@ss", "db": "app",
    }
