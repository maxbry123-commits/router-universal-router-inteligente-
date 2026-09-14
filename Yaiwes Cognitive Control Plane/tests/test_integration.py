import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts import ContextItem, ContextRequest, Evidence, ProposedAction
from source_of_truth import resolve
from consistency_engine import check
from context_composer import compose
from router import select
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
