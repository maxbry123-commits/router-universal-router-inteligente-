"""Adaptadores de agentes. Todos razonan llamando al Router YAIWES."""
from __future__ import annotations

import asyncio
import json
from typing import Any

try:
    from .router_cliente import RouterCliente
except ImportError:
    from router_cliente import RouterCliente


def _decode(raw: str) -> dict:
    try:
        value = json.loads(raw)
        if isinstance(value, dict):
            return value
    except (TypeError, json.JSONDecodeError):
        pass
    return {"approve": False, "status": "REVISE", "issues": ["json"]}


class RouterAgent:
    def __init__(self, client: RouterCliente | None = None) -> None:
        self.client = client or RouterCliente()

    def _ask(self, role: str, payload: Any) -> dict:
        prompt = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return _decode(self.client.chat(prompt, role))


class RowboatDirector(RouterAgent):
    def submit(self, goal: str) -> dict:
        return {"goal": goal, "status": "PLANNING"}


class Hermes(RouterAgent):
    async def plan(self, goal: str) -> dict:
        return self._ask("hermes.plan", {"goal": goal})

    async def critique(self, plan: dict) -> dict:
        return self._ask("hermes.critique", {"plan": plan})

    async def synthesize(self, **payload: Any) -> dict:
        return self._ask("hermes.synthesize", payload)

    async def review(self, task: dict, evidence: dict) -> dict:
        return self._ask("hermes.review", {"task": task, "evidence": evidence})

    async def reconsider(self, task: dict, evidence: dict, other: dict) -> dict:
        return self._ask(
            "hermes.reconsider",
            {"task": task, "evidence": evidence, "other": other},
        )


class OpenClaw(RouterAgent):
    async def plan(self, goal: str) -> dict:
        return self._ask("openclaw.plan", {"goal": goal})

    async def critique(self, plan: dict) -> dict:
        return self._ask("openclaw.critique", {"plan": plan})

    async def review_plan(self, plan: dict) -> dict:
        return self._ask("openclaw.review_plan", {"plan": plan})

    async def review(self, task: dict, evidence: dict) -> dict:
        return self._ask("openclaw.review", {"task": task, "evidence": evidence})

    async def reconsider(self, task: dict, evidence: dict, other: dict) -> dict:
        return self._ask(
            "openclaw.reconsider",
            {"task": task, "evidence": evidence, "other": other},
        )


class RufloAdapter(RouterAgent):
    async def init_swarm(self) -> dict:
        return self._ask(
            "ruflo.init_swarm",
            {"topology": "hierarchical", "strategy": "specialized", "max_agents": 12},
        )

    async def dispatch(self, task: dict) -> dict:
        return self._ask("ruflo.dispatch", task)


class ClaudeArquitecto(RouterAgent):
    async def design(self, objective: str, system: str) -> dict:
        return self._ask("claude.design", {"objective": objective, "system": system})


class GrokEjecutor(RouterAgent):
    async def execute(self, job: dict) -> dict:
        return self._ask("grok.execute", job)

    async def correct(self, job: dict, review: dict) -> dict:
        return self._ask("grok.correct", {"job": job, "review": review})


class ClaudeRevisor(RouterAgent):
    async def review(self, design: dict, result: dict) -> dict:
        return self._ask("claude.review", {"design": design, "result": result})


class MetaReviewer(RouterAgent):
    def __init__(self, role: str, client: RouterCliente | None = None) -> None:
        super().__init__(client)
        self.role = role

    async def review(self, job: dict, result: dict) -> dict:
        return self._ask(self.role, {"job": job, "result": result})


class MetaFixer(RouterAgent):
    async def correct(self, job: dict, findings: list) -> dict:
        return self._ask("meta.fixer", {"job": job, "findings": findings})


class MetaEquipo:
    """Cuatro revisores inspeccionan en paralelo; solo el fixer edita."""

    def __init__(
        self,
        code: MetaReviewer | None = None,
        tests: MetaReviewer | None = None,
        visual: MetaReviewer | None = None,
        adversarial: MetaReviewer | None = None,
        fixer: MetaFixer | None = None,
        client: RouterCliente | None = None,
    ) -> None:
        self.code = code or MetaReviewer("meta.code", client)
        self.tests = tests or MetaReviewer("meta.tests", client)
        self.visual = visual or MetaReviewer("meta.visual", client)
        self.adversarial = adversarial or MetaReviewer("meta.adversarial", client)
        self.fixer = fixer or MetaFixer(client)

    async def review_parallel(self, job: dict, result: dict) -> list[dict]:
        return list(await asyncio.gather(
            self.code.review(job, result),
            self.tests.review(job, result),
            self.visual.review(job, result),
            self.adversarial.review(job, result),
        ))
