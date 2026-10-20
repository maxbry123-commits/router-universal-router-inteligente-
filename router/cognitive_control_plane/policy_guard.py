from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Set
from contracts import ProposedAction

SAFE_READ_CAPABILITIES = {"read", "inspect", "search", "test", "simulate"}

@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    require_sandbox: bool = False


def evaluate(action: ProposedAction, granted_capabilities: Iterable[str] = ()) -> PolicyDecision:
    granted: Set[str] = set(granted_capabilities)
    cap = action.capability
    if cap in SAFE_READ_CAPABILITIES:
        return PolicyDecision(True, "SAFE_CAPABILITY", False)
    # Fail closed: unknown/write/side-effect capability requires explicit grant.
    if cap not in granted:
        return PolicyDecision(False, "CAPABILITY_NOT_GRANTED", action.irreversible)
    if action.irreversible and not action.approved:
        return PolicyDecision(False, "IRREVERSIBLE_REQUIRES_APPROVAL", True)
    if action.irreversible and not action.sandboxed:
        return PolicyDecision(False, "IRREVERSIBLE_REQUIRES_SANDBOX", True)
    return PolicyDecision(True, "EXPLICITLY_GRANTED", action.irreversible)
