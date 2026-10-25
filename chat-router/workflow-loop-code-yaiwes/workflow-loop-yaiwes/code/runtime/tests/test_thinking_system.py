"""ThinkingSystem: mirothinker como slot de razonamiento del orquestador."""
import pytest

from wordflow_loop.thinking_system import ThinkingSystem, ThinkingResult
from wordflow_loop.agent_fleet.agent_fleet_adapter import AgentBindingError


class _StubAdapter:
    def __init__(self, bound=True, response=None):
        self.bound = bound
        self.response = response or {}
        self.payloads = []

    def resolve(self, agent_id=None, role=None):
        if not self.bound:
            raise AgentBindingError("NOT_BOUND")
        return {"agent_id": agent_id}

    def build_invocation_payload(self, agent_id, payload):
        return {"agent_id": agent_id, "task_payload": payload}

    def invoke(self, agent_id, payload, timeout_s=120):
        self.payloads.append(payload)
        return self.response


def test_reason_returns_reasons_evidence_uncertainty():
    stub = _StubAdapter(response={
        "reasons": ["option A is cheaper"],
        "evidence": [{"kind": "test", "ref": "/e"}],
        "uncertainty": ["rate limit unknown"],
        "status": "REASONED",
    })
    ts = ThinkingSystem(adapter=stub)
    res = ts.reason("pick component", options=[{"id": "a"}])
    assert isinstance(res, ThinkingResult)
    assert res.agent_id == "mirothinker"
    assert res.reasons == ["option A is cheaper"]
    assert res.uncertainty == ["rate limit unknown"]
    payload = stub.payloads[0]["task_payload"]
    assert payload["mode"] == "reasoning"
    assert any("no autorices" in c for c in payload["constraints"])


def test_reason_fail_closed_when_agent_not_bound():
    ts = ThinkingSystem(adapter=_StubAdapter(bound=False))
    with pytest.raises(RuntimeError, match="THINKING_AGENT_NOT_BOUND"):
        ts.reason("anything")


def test_reason_passes_evidence_state():
    stub = _StubAdapter(response={"reasons": []})
    ts = ThinkingSystem(adapter=stub)
    ts.reason("g", evidence_state={"ledger_seq": 7})
    assert stub.payloads[0]["task_payload"]["evidence_state"]["ledger_seq"] == 7
