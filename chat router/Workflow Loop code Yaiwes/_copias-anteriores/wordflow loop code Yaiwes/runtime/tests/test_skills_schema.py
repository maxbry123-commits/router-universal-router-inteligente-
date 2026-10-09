"""N-1.5: 24 skills a schema DSL DAG — validación estructural obligatoria."""
from pathlib import Path

import yaml

_SCHEMAS = Path(__file__).resolve().parents[2] / "skills_schema"
_REQUIRED = {"schema_id", "schema", "objective", "work_surface",
             "acceptance", "tools", "evidence", "oracle", "gap_policy", "nodes"}
_ALL = sorted(p.name for p in _SCHEMAS.glob("*.dag.yaml"))


def test_24_schemas_present():
    assert len(_ALL) == 24, f"faltan schemas: {_ALL}"


def test_cada_schema_campos_obligatorios():
    for name in _ALL:
        d = yaml.safe_load((_SCHEMAS / name).read_text())
        missing = _REQUIRED - set(d)
        assert not missing, f"{name} le faltan {missing}"
        assert d["schema"] == "yaiwes.skill-dag/v1"
        assert d["oracle"], f"{name} sin oracle"
        assert d["acceptance"], f"{name} sin acceptance"


def test_skill_router_es_punto_de_entrada():
    d = yaml.safe_load((_SCHEMAS / "skill-router.dag.yaml").read_text())
    assert "router" in d["oracle"] or "entry" in d["objective"].lower() or "punto" in d["objective"].lower()


def test_meta_schema_skill_creator_primero():
    d = yaml.safe_load((_SCHEMAS / "skill-creator.dag.yaml").read_text())
    assert "meta" in d["oracle"] or "PRIMERO" in str(d["acceptance"])
