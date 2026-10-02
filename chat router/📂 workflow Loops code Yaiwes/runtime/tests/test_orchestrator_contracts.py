"""O4-06: contratos normalizados del orquestador."""
import pytest

from wordflow_loop.contracts import Status
from wordflow_loop.orchestrator_contracts import (
    EvidenceRecord, MissionAuthority, MissionContract, OracleStatus,
    OracleVerdict, ResultEnvelope, TaskContract)


def test_mission_only_hermes_creates():
    m = MissionContract.build("m1", "cerrar backend", MissionAuthority.HERMES)
    assert m.goal_sha256 and m.created_by == MissionAuthority.HERMES
    with pytest.raises(PermissionError):
        MissionContract.build("m2", "x", MissionAuthority.SHERIFF)


def test_task_contract_sha_stable():
    t1 = TaskContract("t1", "m1", "n1", "writer", {"file": "a.py"})
    assert t1.sha() == t1.sha()
    t2 = TaskContract("t1", "m1", "n1", "writer", {"file": "b.py"})
    assert t1.sha() != t2.sha()


def test_oracle_verdict_no_pass_sin_evidencia():
    v = OracleVerdict(OracleStatus.PASS)
    assert not v.valid()
    v2 = OracleVerdict(OracleStatus.PASS, evidence=(EvidenceRecord("/e", "test", "ab" * 32),))
    assert v2.valid()
    v3 = OracleVerdict(OracleStatus.BLOCKED)
    assert v3.valid()


def test_result_envelope_sealed_receipt():
    env = ResultEnvelope("t1", "m1", "n1", Status.PASS,
                         evidence=(EvidenceRecord("/e", "test", "cd" * 32),))
    sealed = env.sealed()
    assert sealed.receipt_sha256
    assert sealed.sealed().receipt_sha256 == sealed.receipt_sha256
