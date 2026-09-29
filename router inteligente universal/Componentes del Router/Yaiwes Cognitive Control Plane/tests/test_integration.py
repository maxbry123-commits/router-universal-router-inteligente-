import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts import ContextItem, ContextRequest, Evidence, ProposedAction, INPUT_SHARK_RESOLUTION
from source_of_truth import resolve
from consistency_engine import check
from context_composer import compose
from router import select, retrieve
from policy_guard import evaluate


def test_fail_closed_decision_path():
    evidence=[Evidence("test","PASS"), Evidence("runtime","FAIL")]
    truth=resolve(evidence)
    assert truth.selected is not None and truth.selected.value == "FAIL"
    consistent=check(evidence)
    assert (consistent.state, consistent.action) == ("CONFLICTED","RECONCILE")
    routes=select("runtime fail contradicts CI pass; reconcile decision", parallel_width=3)
    assert routes
    pack=compose(ContextRequest("i1","q",[ContextItem("e1","runtime reports FAIL",1,"runtime",1),ContextItem("e2","CI reports PASS",.8,"test",1)],128))
    assert pack.estimated_tokens <= 128
    gate=evaluate(ProposedAction("push-fix","write_repo"))
    assert not gate.allowed


def test_indexed_dataset_to_context_pipeline():
    routes=select("recovery after crash needs evidence", parallel_width=2)
    assert routes
    rows=retrieve("Y26", category_limits={"debugging":2,"causal":1,"error":1,"counterexample":1})
    assert len(rows)==5
    items=[ContextItem(r["id"], r["problem"]+" | "+" ; ".join(r["correct_method"]), .9, "repo", .9) for r in rows]
    pack=compose(ContextRequest("i2","recovery",items,800))
    assert len(pack.selected)==5
    assert pack.estimated_tokens <= 800
    assert {r["method_id"] for r in rows} == {"Y26"}


def test_policy_guard_requires_grant_approval_and_sandbox_for_irreversible_write():
    action=ProposedAction("publish","write_repo",irreversible=True,sandboxed=False,approved=False)
    denied=evaluate(action, granted_capabilities=[])
    assert not denied.allowed and denied.reason=="CAPABILITY_NOT_GRANTED"
    approved=ProposedAction("publish","write_repo",irreversible=True,sandboxed=True,approved=True)
    allowed=evaluate(approved, granted_capabilities=["write_repo"])
    assert allowed.allowed and allowed.reason=="EXPLICITLY_GRANTED"


def test_input_shark_remains_external():
    assert INPUT_SHARK_RESOLUTION["fusion"] is False
    assert INPUT_SHARK_RESOLUTION["context_composer_contract"] == "ContextRequest -> ContextPack"
