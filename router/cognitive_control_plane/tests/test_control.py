import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts import ContextItem, ContextRequest, Evidence, ProposedAction
from source_of_truth import resolve
from context_composer import compose
from consistency_engine import check
from policy_guard import evaluate


def test_source_of_truth_runtime_wins():
    r = resolve([Evidence("llm_text", "PASS"), Evidence("runtime", "FAIL")])
    assert r.selected is not None and r.selected.source == "runtime" and r.selected.value == "FAIL"


def test_context_budget_and_dedup():
    req = ContextRequest("r1", "q", [ContextItem("1", "same text", 1, "runtime", 1), ContextItem("2", "same text", .1, "repo", .1)], 10)
    p = compose(req)
    assert len(p.selected) == 1 and p.estimated_tokens <= 10


def test_conflict_reconciles():
    r = check([Evidence("test", "PASS"), Evidence("runtime", "FAIL")])
    assert r.state == "CONFLICTED" and r.action == "RECONCILE"


def test_policy_fail_closed():
    d = evaluate(ProposedAction("push", "write_repo"))
    assert not d.allowed and d.reason == "CAPABILITY_NOT_GRANTED"


def test_irreversible_requires_approval_and_sandbox():
    a = ProposedAction("deploy", "deploy", irreversible=True, sandboxed=False, approved=False)
    assert not evaluate(a, ["deploy"]).allowed
