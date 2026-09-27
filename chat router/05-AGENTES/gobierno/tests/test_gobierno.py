"""Tests del gobierno T01 (pytest). Mínimo 3 casos por clase: PASS y fallos."""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from agent_control import (AgentDAG, AgentDSL, AgentOrchestrator, EvidenceVerifier, Guardian, Investigator, SchemaValidator)  # noqa: E402
from contratos import Job, Result, State, Task  # noqa: E402
from judge import Judge  # noqa: E402
from mirror_manager import SYSTEM_MAP, MirrorManager  # noqa: E402
from sentinel import Sentinel  # noqa: E402
from sentinel_loop import (SentinelDAG, SentinelDSL, SentinelOrchestrator, SentinelResearchPlanner, SentinelSchemaValidator, SentinelSheriff, SentinelVerifier, SentinelGuardian, update_state)  # noqa: E402
from sheriff import Sheriff  # noqa: E402


# ---------------- contratos ----------------

class TestContratos:
    def test_job_roundtrip(self):
        job = Job(job_id="UI-001", objective="editor", acceptance=["drag"])
        d = job.to_dict()
        assert Job.from_dict(d).to_dict() == d

    def test_job_falta_obligatorio(self):
        with pytest.raises(ValueError):
            Job.from_dict({"objective": "x"})
        with pytest.raises(ValueError):
            Job(job_id="", objective="x")

    def test_result_roundtrip_y_status(self):
        r = Result(job_id="J1", agent="grok_executor", status="PASS",
                   next_action="CLAUDE_REVIEW")
        assert Result.from_dict(r.to_dict()).agent == "grok_executor"
        with pytest.raises(ValueError):
            Result(job_id="J1", agent="a", status="QUIZAS")

    def test_task_y_state(self):
        t = Task(id="t1", objective="o", role="coder", dependencies=["t0"])
        assert Task.from_dict(t.to_dict()).dependencies == ["t0"]
        assert State.JUDGMENT.value == "JUDGMENT"
        with pytest.raises(ValueError):
            Task.from_dict({"id": "t1"})


# ---------------- sheriff ----------------

class TestSheriff:
    def setup_method(self):
        self.s = Sheriff()

    def test_plan_valido(self):
        plan = {"tasks": [
            {"id": "a", "acceptance": ["ok"], "allowed_paths": ["src/"]},
            {"id": "b", "acceptance": ["ok"], "dependencies": ["a"]},
        ]}
        assert self.s.validate(plan) == (True, "PASS")

    def test_sin_acceptance(self):
        plan = {"tasks": [{"id": "a"}]}
        ok, motivo = self.s.validate(plan)
        assert not ok and "aceptación" in motivo

    def test_dependencia_invalida(self):
        plan = {"tasks": [{"id": "a", "acceptance": ["x"],
                           "dependencies": ["fantasma"]}]}
        ok, motivo = self.s.validate(plan)
        assert not ok and "Dependencia" in motivo

    def test_rutas_prohibidas(self):
        for ruta in ("/abs", "../traversal", ".github/workflows/x",
                     "router inteligente universal/secreto"):
            plan = {"tasks": [{"id": "a", "acceptance": ["x"],
                               "allowed_paths": [ruta]}]}
            ok, _ = self.s.validate(plan)
            assert not ok, ruta


# ---------------- judge ----------------

class TestJudge:
    def setup_method(self):
        self.j = Judge()
        self.ok = {"approve": True}

    def test_pass(self):
        ev = {"status": "PASS", "tests": ["t1"]}
        assert self.j.decide({}, ev, self.ok, self.ok) == "PASS"

    def test_revise_sin_evidencia_o_tests(self):
        assert self.j.decide({}, {}, self.ok, self.ok) == "REVISE"
        assert self.j.decide({}, {"status": "PASS"}, self.ok, self.ok) == "REVISE"

    def test_revise_si_revisor_rechaza(self):
        ev = {"status": "PASS", "tests": ["t"]}
        assert self.j.decide({}, ev, {"approve": False}, self.ok) == "REVISE"

    def test_block_unauthorized(self):
        ev = {"status": "PASS", "tests": ["t"], "unauthorized_change": True}
        assert self.j.decide({}, ev, self.ok, self.ok) == "BLOCK"


# ---------------- sentinel ----------------

class TestSentinel:
    def test_continue(self):
        assert Sentinel().inspect({"status": "RUNNING"}) == {"action": "CONTINUE"}

    def test_error_recover_y_reassign_a_la_tercera(self):
        s = Sentinel()
        estado = {"status": "ERROR", "error": "boom"}
        assert s.inspect(estado) == {"action": "RECOVER"}
        assert s.inspect(estado) == {"action": "RECOVER"}
        assert s.inspect(estado) == {"action": "REASSIGN"}

    def test_stalled_y_unauthorized(self):
        s = Sentinel()
        assert s.inspect({"status": "STALLED"}) == {"action": "REASSIGN"}
        assert s.inspect({"unauthorized_change": True}) == {"action": "BLOCK"}

    def test_heartbeat_viejo(self):
        viejo = (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat()
        assert Sentinel().inspect({"status": "RUNNING", "heartbeat_at": viejo}) == {
            "action": "REASSIGN"}
        fresco = datetime.now(timezone.utc).isoformat()
        assert Sentinel().inspect({"status": "RUNNING", "heartbeat_at": fresco}) == {
            "action": "CONTINUE"}


# ---------------- mirror manager ----------------

@pytest.fixture
def repo_git(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-m", "init"], cwd=repo, check=True,
                   capture_output=True)
    return repo


class TestMirrorManager:
    def test_create_worktree(self, repo_git):
        mm = MirrorManager(repo_git)
        m = mm.create("job-1", "router")
        assert Path(m["workspace"]).is_dir()
        assert m["allowed_paths"] == SYSTEM_MAP["router"]["paths"]

    def test_sistema_desconocido(self, repo_git):
        with pytest.raises(ValueError):
            MirrorManager(repo_git).create("job-x", "no-existe")

    def test_diff_y_merge_selectivo(self, repo_git):
        mm = MirrorManager(repo_git)
        m = mm.create("job-2", "memory")
        nuevo = Path(m["workspace"]) / "memory" / "nota.txt"
        nuevo.parent.mkdir(parents=True, exist_ok=True)
        nuevo.write_text("cambio\n")
        ok, motivo = mm.merge_selectivo("job-2", Sheriff())
        assert ok, motivo
        assert (repo_git / "memory" / "nota.txt").read_text() == "cambio\n"

    def test_merge_bloqueado_por_sheriff(self, repo_git):
        mm = MirrorManager(repo_git)
        m = mm.create("job-3", "router")
        prohibido = Path(m["workspace"]) / ".github" / "x.yml"
        prohibido.parent.mkdir(parents=True, exist_ok=True)
        prohibido.write_text("mal\n")
        ok, motivo = mm.merge_selectivo("job-3", Sheriff())
        assert not ok and "prohibida" in motivo
        mm.keep_for_debug("job-3")
        assert mm.mirrors["job-3"]["debug"] is True


# ---------------- control del agente ----------------

class TestAgentControl:
    def _spec(self):
        return AgentDSL.parse({
            "task_id": "T01",
            "objective": "gobierno",
            "scope": "chat router/05-AGENTES/gobierno",
            "required_files": ["mirror_manager.py", "tests/test_gobierno.py"],
            "acceptance_commands": [
                'python -m pytest "chat router/05-AGENTES/gobierno" -q'
            ],
        })

    def test_dsl_schema_y_dag(self):
        spec = self._spec()
        assert SchemaValidator().validate(spec) == (True, "PASS")
        dag = AgentDAG.build(spec)
        assert ("VERIFY", "GUARDIAN") in dag["edges"]
        with pytest.raises(ValueError):
            AgentDSL.parse({"task_id": "T01"})

    def test_verificador_no_admite_falso_verde(self):
        spec = self._spec()
        verifier = EvidenceVerifier()
        ok, issues = verifier.verify(spec, {
            "files": [],
            "test_exit_code": 5,
            "tests_collected": 0,
        })
        assert not ok
        assert "no_tests_collected" in issues
        assert any(i.startswith("missing_files:") for i in issues)

    def test_guardian_scope_y_git_sucio(self):
        spec = self._spec()
        guardian = Guardian()
        assert guardian.inspect(spec, {
            "changed_files": [".github/x.yml"]
        })["action"] == "BLOCK"
        assert guardian.inspect(spec, {
            "changed_files": [],
            "sync_attempted": True,
            "dirty_worktree": True,
        })["action"] == "REVISE"

    def test_investigador_maximo_20_fuentes(self):
        spec = self._spec()
        packet = Investigator.prepare(
            spec, "merge failed", {"tool": "git", "version": "2.55"}
        )
        assert packet["max_sources"] == 20
        assert "root_cause" in packet["required_output"]

    def test_orquestador_pass_revise_research(self):
        spec = self._spec()
        orch = AgentOrchestrator()
        passed = {
            "files": ["mirror_manager.py", "tests/test_gobierno.py"],
            "test_exit_code": 0,
            "tests_collected": 25,
        }
        assert orch.next_action(spec, passed)["state"] == "PASS"
        revise = orch.next_action(
            spec, {"files": [], "test_exit_code": 1, "tests_collected": 25},
            attempt=1,
        )
        assert revise["state"] == "REVISE"
        research = orch.next_action(
            spec, {"files": [], "test_exit_code": 1, "tests_collected": 25},
            attempt=3,
        )
        assert research["state"] == "RESEARCH"


# ---------------- LOOP común de sentinelas ----------------

class TestSentinelLoop:
    def _spec(self):
        return SentinelDSL.parse({
            "sentinel_id": "sentinela-chat",
            "objective": "cerrar T01 con evidencia",
            "repository": "owner/repo",
            "report_path": "chat router/06-EQUIPO/SENTINELA-chat.md",
            "priority_goals": ["T01"],
            "evidence_required": ["head_fresh", "priority_goal_observed"],
            "research_sources": [f"fuente-{i}" for i in range(25)],
            "max_attempts": 3,
            "max_research_sources": 20,
        })

    def test_schema_dag_y_sheriff_compartidos(self):
        spec = self._spec()
        assert SentinelSchemaValidator().validate(spec) == (True, "PASS")
        dag = SentinelDAG.build(spec)
        assert ("ORDER", "EXECUTOR") in dag["edges"]
        sheriff = SentinelSheriff()
        assert sheriff.validate_write_paths([spec.report_path]) == (True, "PASS")
        assert sheriff.validate_write_paths(["src/app.py"])[0] is False

    def test_verifier_y_guardian_frescura(self):
        spec = self._spec()
        verifier = SentinelVerifier()
        ok, issues = verifier.verify(spec, {
            "observed_sha": "abc",
            "current_sha": "abc",
            "executor_active": False,
            "workflow_false_green": False,
            "objective_evidence": {
                "head_fresh": True,
                "priority_goal_observed": True,
            },
        })
        assert ok and issues == []
        stale = SentinelGuardian().inspect(
            spec, {"attempt": 0},
            {"observed_sha": "abc", "current_sha": "def"},
        )
        assert stale["action"] == "REOBSERVE"

    def test_research_max_20_y_memoria_loop(self):
        spec = self._spec()
        packet = SentinelResearchPlanner.build(
            spec, "TESTS_FALLAN", "FAILED test_merge"
        )
        assert packet["max_sources"] == 20
        assert len(packet["sources"]) == 20

        state = update_state(
            {"attempt": 1, "last_failure": "TESTS_FALLAN", "same_failure_count": 1},
            {"state": "REVISE", "reason": "TESTS_FALLAN"},
            {"current_sha": "abc", "failure_class": "TESTS_FALLAN"},
        )
        assert state["attempt"] == 2
        assert state["same_failure_count"] == 2

    def test_orquestador_pass_active_revise(self):
        spec = self._spec()
        orch = SentinelOrchestrator()
        base = {
            "observed_sha": "abc",
            "current_sha": "abc",
            "executor_active": False,
            "workflow_false_green": False,
            "objective_evidence": {
                "head_fresh": True,
                "priority_goal_observed": True,
            },
        }
        assert orch.next_action(spec, {"attempt": 0}, base)["state"] == "PASS"
        active = dict(base, executor_active=True)
        assert orch.next_action(spec, {"attempt": 0}, active)["state"] == "ACTIVE"
        bad = dict(base)
        bad["objective_evidence"] = {"head_fresh": True, "priority_goal_observed": False}
        assert orch.next_action(spec, {"attempt": 0}, bad)["state"] == "REVISE"
