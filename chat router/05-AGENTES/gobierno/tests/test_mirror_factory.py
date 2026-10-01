"""Tests de mirror_factory (T11-F): scopes aislados, sin elevación, autoridad única."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

import mirror_factory as mf


def test_dos_mirrors_scopes_aislados():
    f = mf.MirrorFactory()
    f.create("m1", "n1", "root", "w1", ["proyecto-a/"], "sha1", now=10.0)
    f.create("m2", "n2", "root", "w2", ["proyecto-b/"], "sha1", now=10.0)
    man = f.manifest()
    assert man["schema"] == "yaiwes.mirror/v1"
    assert len(man["mirrors"]) == 2
    with pytest.raises(mf.LeaseError, match="SCOPE_OVERLAP"):
        f.create("m3", "n3", "root", "w3", ["proyecto-a/sub/"], "sha1", now=10.0)


def test_hijo_no_eleva_permisos_sobre_padre():
    f = mf.MirrorFactory()
    with pytest.raises(mf.LeaseError, match="SCOPE_ELEVATION"):
        f.create("m1", "n1", "root", "w1", ["/etc"], "sha1",
                 parent_scopes=["proyecto/"], now=10.0)
    rec = f.create("m2", "n2", "root", "w1", ["proyecto/hijo/"], "sha1",
                   parent_scopes=["proyecto/"], now=10.0)
    assert rec["adapters"]["sheriff"] == "central"
    with pytest.raises(mf.LeaseError):
        f.side_effect("m2", "fuera/de/scope", now=10.0)


def test_autoridad_final_unica_y_registro_hijos():
    f = mf.MirrorFactory()
    rec = f.create("m1", "n1", "root", "w1", ["p/"], "sha1", now=10.0)
    for campo in ("parent_id", "mirror_id", "node_id", "claim_id", "scopes", "heartbeat"):
        assert campo in rec
    assert rec["adapters"] == {"sheriff": "central", "judge": "central"}
    assert rec["children"]["hermes_child"].startswith("m1")
    hb = f.heartbeat("m1", now=20.0)
    assert hb["heartbeat"] == 20.0
    with pytest.raises(mf.LeaseError, match="MIRROR_UNKNOWN"):
        f.heartbeat("fantasma", now=20.0)
