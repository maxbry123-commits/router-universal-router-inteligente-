"""Tests skill_runtime (T11-I): contract states, sheriff gate, adapter+evidence required."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.chat_mvp import skill_runtime as sr


def _spec(status="EXECUTABLE", **kw):
    spec = {"id": "s1", "name": "S", "classification": {"kind": "tool"},
            "inputs": {}, "outputs": {}, "permissions": {"write_paths": ["out/"]},
            "status": status, "tools_allowed": ["shell"], "adapter": {"entrypoint": "x:run"}}
    spec.update(kw)
    return spec


def _inv(**kw):
    base = {"skill_id": "s1", "project_id": "p", "task_id": "t", "input": {},
            "allowed_tools": ("shell",), "write_scope": ("out/a",), **kw}
    return sr.SkillInvocation(**base)


def test_executable_requires_adapter_and_evidence():
    reg = sr.SkillRegistry()
    with pytest.raises(sr.SkillContractError, match="sin adapter"):
        sr.register_from_spec(reg, _spec())
    ok = lambda inv: sr.SkillResult("s1", "OK", {}, [{"e": 1}], [])
    sr.register_from_spec(reg, _spec(), adapters={"s1": ok})
    assert reg.invoke(_inv(), sr.sheriff_skill_check).status == "OK"
    bad = lambda inv: sr.SkillResult("s1", "OK", {}, [], [])
    reg2 = sr.SkillRegistry()
    sr.register_from_spec(reg2, _spec(id="s2"), adapters={"s2": bad})
    with pytest.raises(sr.SkillContractError, match="missing evidence"):
        reg2.invoke(_inv(skill_id="s2"), sr.sheriff_skill_check)


def test_documentation_only_not_invocable():
    reg = sr.SkillRegistry()
    sr.register_from_spec(reg, _spec(status="DOCUMENTATION_ONLY"))
    with pytest.raises(sr.SkillContractError, match="not executable"):
        reg.invoke(_inv(), sr.sheriff_skill_check)


def test_sheriff_blocks_extra_tools_and_scope():
    assert not sr.sheriff_skill_check(_spec(), _inv(allowed_tools=("shell", "network")))
    assert not sr.sheriff_skill_check(_spec(), _inv(write_scope=("etc/passwd",)))
    assert sr.sheriff_skill_check(_spec(), _inv())


def test_compile_rejects_missing_and_bad_status():
    with pytest.raises(sr.SkillContractError, match="missing fields"):
        sr.compile_skill({"id": "x"})
    with pytest.raises(sr.SkillContractError, match="unknown status"):
        sr.compile_skill(_spec(status="INVENTED"))
    with pytest.raises(sr.SkillContractError, match="entrypoint"):
        sr.compile_skill(_spec(adapter={}))
