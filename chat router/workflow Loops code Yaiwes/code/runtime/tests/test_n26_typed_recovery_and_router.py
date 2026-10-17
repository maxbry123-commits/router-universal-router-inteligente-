"""N-2.5/N-2.6/N-2.7: recovery tipado, stuck detector, router FAIL_CLOSED."""
import warnings

from src.recovery.engine import RecoveryEngine
from src.core.task_runtime import FailureKind
from src.agent.agent_router import AgentRouter


def _engine(max_repeats=3):
    return RecoveryEngine(max_repeats=max_repeats)


def test_typed_recovery_all_kinds_have_policy():
    e = _engine()
    cases = {
        "timeout while fetching": FailureKind.RETRYABLE,
        "HTTP 429 too many requests": FailureKind.RETRYABLE,
        "unauthorized token": FailureKind.AUTH,
        "jsonschema validationerror": FailureKind.DEPENDENCY,
        "out of memory": FailureKind.CRASH,
        "some unknown crash": FailureKind.IRREVERSIBLE,
    }
    for msg, kind in cases.items():
        assert e.classify_kind(msg) == kind, msg


def test_retryable_retries_then_escalates():
    e = _engine()
    r1 = e.handle_failure("n1", "timeout", attempt=1, current_state={}, action_type="fetch")
    assert r1["action"] == "RETRY" and r1["kind"] == FailureKind.RETRYABLE
    r4 = e.handle_failure("n1", "timeout", attempt=3, current_state={"x": 1}, action_type="fetch2")
    assert r4["action"] in {"NON_RETRYABLE", "ESCALATE_TO_DIRECTOR", "BLOCKED_STUCK"}


def test_auth_never_retries_and_escalates():
    e = _engine()
    r = e.handle_failure("n1", "401 unauthorized", attempt=1, current_state={})
    assert r["kind"] == FailureKind.AUTH
    assert r["action"] == "ESCALATE_TO_DIRECTOR"
    assert r["next_state"] == "BLOCKED_AUTH"


def test_stuck_detector_blocks_after_repeats():
    e = _engine(max_repeats=3)
    for i in range(2):
        r = e.handle_failure("n1", "timeout", attempt=1, current_state={"s": 1}, action_type="op")
        assert r["action"] == "RETRY"
    r = e.handle_failure("n1", "timeout", attempt=1, current_state={"s": 1}, action_type="op")
    assert r["action"] == "BLOCKED_STUCK"
    assert r["kind"] == FailureKind.STUCK
    assert r["next_state"] == "STRATEGY_CHANGE"


def test_new_evidence_resets_stuck_counter():
    e = _engine(max_repeats=3)
    e.handle_failure("n1", "timeout", attempt=1, current_state={"s": 1}, action_type="op")
    e.handle_failure("n1", "timeout", attempt=1, current_state={"s": 1}, action_type="op")
    r = e.handle_failure("n1", "timeout", attempt=1, current_state={"s": 2},
                       action_type="op", new_evidence=True)
    assert r["action"] == "RETRY"


def test_agent_router_fail_closed_no_match():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        router = AgentRouter()
    res = router.select_agent("coding", ["skill_that_no_agent_has_xyz"])
    assert res["status"] == "FAIL_CLOSED"
    assert res["selected_agent_id"] is None


def test_agent_router_real_match_binds_via_adapter():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        router = AgentRouter()
    res = router.select_agent("writer", ["executor"])
    assert res["status"] == "ROUTED"
    assert res["selected_agent_id"] == "opencode"
    assert res["binding"]["agent_id"] == "opencode"
