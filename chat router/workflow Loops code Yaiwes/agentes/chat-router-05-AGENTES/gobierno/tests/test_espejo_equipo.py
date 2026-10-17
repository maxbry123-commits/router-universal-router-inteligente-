"""Tests de espejo_equipo (pytest)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

import espejo_equipo as E  # noqa: E402

MAN = """
codigo_descargado: "comp/"
jerarquia:
  - {id: hermes, carpeta: hermes/}
  - {id: openclaw, carpeta: openclaw/}
  - {id: ruflo, codigo: "Componente…/ruflo", carpeta: ruflo/}
  - {id: fantasma, carpeta: nada/}
apoyo: [ {id: codex} ]
"""


def _repo(tmp_path, man=MAN):
    o = tmp_path / "o"
    a = o / "chat router" / "05-AGENTES"
    for d in ("hermes", "openclaw", "ruflo", "asistentes", "Banco de claves"):
        (a / d).mkdir(parents=True)
    (a / "AGENTES.yaml").write_text(man, encoding="utf-8")
    (a / "hermes" / "a.md").write_text("hola")
    (a / "hermes" / "k.enc").write_text("x")
    (a / "hermes" / ".env").write_text("x")
    (a / "hermes" / "t.txt").write_text("k=nvapi-" + "A" * 30)
    (a / "hermes" / "big.bin").write_bytes(b"0" * (E.MAX_BYTES + 1))
    (a / "openclaw" / "b.md").write_text("oc")
    (a / "ruflo" / "r.md").write_text("ru")
    (a / "asistentes" / "hermes.md").write_text("puente")
    (a / "Banco de claves" / "x.txt").write_text("x")
    return o


def test_dry_run_no_copia(tmp_path):
    o, d = _repo(tmp_path), tmp_path / "d"
    assert E.main(["--modo", "equipo_completo", "--origen", str(o), "--destino", str(d)]) == 0
    assert not d.exists()


def test_modos_distintos_y_missing(tmp_path):
    o = _repo(tmp_path)
    h = E.planificar("hermes_openclaw", o)
    c = E.planificar("equipo_completo", o)
    ph, pc = {f["path"] for f in h["archivos"]}, {f["path"] for f in c["archivos"]}
    assert any(p.endswith("hermes/a.md") for p in ph) and not any("ruflo" in p for p in ph)
    assert any("ruflo/r.md" in p for p in pc) and ph < pc
    assert any(p.endswith("asistentes/hermes.md") for p in ph)
    assert {"hermes", "puente"} <= {m["agente"] for m in h["missing"]} | {"puente", "hermes"}
    assert any(m["agente"] == "fantasma" for m in c["missing"])
    assert any(m["agente"] == "codex" and m["ruta"] is None for m in c["missing"])


def test_secretos_excluidos(tmp_path):
    o, d = _repo(tmp_path), tmp_path / "d"
    plan = E.planificar("equipo_completo", o)
    E.aplicar(plan, d)
    copiados = {p.name for p in d.rglob("*") if p.is_file()}
    assert not copiados & {"k.enc", ".env", "t.txt", "big.bin"}
    assert not any("Banco de claves" in str(p) for p in d.rglob("*"))
    razones = {e["razon"] for e in plan["excluidos"]}
    assert {"patron_secreto_nombre", "contenido_tipo_secreto", "mayor_5MB"} <= razones


def test_path_traversal_refusado(tmp_path):
    o = _repo(tmp_path, MAN.replace("carpeta: hermes/", "carpeta: ../../../../etc/"))
    plan = E.planificar("hermes_openclaw", o)
    assert plan["refused"] and plan["refused"][0]["razon"] == "path_traversal"
    with pytest.raises(ValueError):
        E.aplicar({"origen": str(o), "modo": "x", "archivos": [{"path": "../evil"}], "excluidos": [], "missing": [], "refused": []}, tmp_path / "d")


def test_manifest_hashes(tmp_path):
    import hashlib
    o, d = _repo(tmp_path), tmp_path / "d"
    E.aplicar(E.planificar("hermes_openclaw", o), d, commit="abc")
    mm = json.loads((d / "MIRROR-MANIFEST.json").read_text())
    assert mm["modo"] == "hermes_openclaw" and mm["source_commit"] == "abc" and mm["files"]
    for f in mm["files"]:
        assert f["sha256"] == hashlib.sha256((d / f["path"]).read_bytes()).hexdigest()
        assert not (d / f["path"]).is_symlink()
