"""Small, fail-closed contract for the nine-worker GitHub queue."""

import graphlib
from pathlib import PurePosixPath
import re

ROOT = "router inteligente universal/agents-yaiwes"
CONTROL = (".git", ".github", "ops/yaiwes", ROOT,
           "router inteligente universal/Banco de claves",
           "router inteligente universal/agent-microkernel",
           "chat router/03-ESTADO")
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]+\Z")


def path(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("INVALID_PATH")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(p in (".", "..") for p in value.split("/")) or str(parsed) != value:
        raise ValueError("INVALID_PATH")
    if any(value == p or value.startswith(p + "/") for p in CONTROL):
        raise ValueError("CONTROL_PATH")
    if any(part.startswith(".env") for part in parsed.parts):
        raise ValueError("SECRET_PATH")
    return value


def validate(chain, agent_id, request_id):
    if not IDENTIFIER.fullmatch(agent_id) or not IDENTIFIER.fullmatch(request_id):
        raise ValueError("INVALID_ID")
    if not isinstance(chain, dict) or set(chain) != {
        "schema", "request_id", "agent", "input_block", "write_scope", "tests", "steps", "edges"
    }:
        raise ValueError("INVALID_SCHEMA")
    if chain["schema"] != "yaiwes.chain/v2" or chain["request_id"] != request_id:
        raise ValueError("INVALID_REQUEST")
    if chain["agent"] != {"id": agent_id, "framework": "openai-agents"}:
        raise ValueError("INVALID_AGENT")
    if not isinstance(chain["input_block"], str) or not chain["input_block"].strip():
        raise ValueError("INVALID_INSTRUCTION")
    scope = chain["write_scope"]
    if (not isinstance(scope, list) or not scope or
            any(not isinstance(s, str) for s in scope) or len(scope) != len(set(scope))):
        raise ValueError("INVALID_SCOPE")
    for item in scope:
        path(item)
    tests = chain["tests"]
    if not isinstance(tests, list) or not tests or any(
        not isinstance(argv, list) or not argv or
        any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv)
        for argv in tests
    ):
        raise ValueError("INVALID_TESTS")
    steps = chain["steps"]
    if not isinstance(steps, list) or not steps or any(
        not isinstance(step, dict) or set(step) != {"id", "task"} or
        not isinstance(step["id"], str) or not IDENTIFIER.fullmatch(step["id"]) or
        not isinstance(step["task"], str) or not step["task"].strip()
        for step in steps
    ):
        raise ValueError("INVALID_STEPS")
    ids = [step["id"] for step in steps]
    if len(set(ids)) != len(ids):
        raise ValueError("DUPLICATE_STEPS")
    edges = chain["edges"]
    if not isinstance(edges, list) or any(
        not isinstance(edge, list) or len(edge) != 2 or
        edge[0] not in ids or edge[1] not in ids for edge in edges
    ):
        raise ValueError("INVALID_EDGES")
    graph = {sid: set() for sid in ids}
    for before, after in edges:
        graph[after].add(before)
    try:
        return list(graphlib.TopologicalSorter(graph).static_order())
    except graphlib.CycleError as exc:
        raise ValueError("CYCLE") from exc


def in_scope(name, scope):
    path(name)
    return any(name == s or name.startswith(s.rstrip("/") + "/") for s in scope)
