"""YaiwesHive (doc 23) + EngineeringLoop (doc 22)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

try:
    from .agentes import (
        ClaudeArquitecto,
        ClaudeRevisor,
        GrokEjecutor,
        Hermes,
        MetaEquipo,
        OpenClaw,
        RowboatDirector,
        RufloAdapter,
    )
except ImportError:
    from agentes import (
        ClaudeArquitecto,
        ClaudeRevisor,
        GrokEjecutor,
        Hermes,
        MetaEquipo,
        OpenClaw,
        RowboatDirector,
        RufloAdapter,
    )

GOBIERNO = Path(__file__).resolve().parents[1] / "gobierno"
if str(GOBIERNO) not in sys.path:
    sys.path.insert(0, str(GOBIERNO))

try:
    from judge import Judge
    from sentinel import Sentinel
    from sheriff import Sheriff
except ImportError:  # TODO T01: fallback solo para repos sin gobierno instalado
    class Sheriff:
        def validate(self, plan):
            return (bool(plan.get("tasks")), "PASS" if plan.get("tasks") else "plan sin tareas")

    class Sentinel:
        def inspect(self, state):
            return {"action": "BLOCK" if state.get("unauthorized_change") else "CONTINUE"}

    class Judge:
        def decide(self, task, evidence, hermes_review, openclaw_review):
            if (
                evidence.get("status") == "PASS"
                and evidence.get("tests")
                and hermes_review.get("approve")
                and openclaw_review.get("approve")
            ):
                return "PASS"
            return "REVISE"


class YaiwesHive:
    def __init__(
        self,
        rowboat=None,
        ruflo=None,
        hermes=None,
        openclaw=None,
        sheriff=None,
        sentinel=None,
        judge=None,
    ) -> None:
        self.rowboat = rowboat or RowboatDirector()
        self.ruflo = ruflo or RufloAdapter()
        self.hermes = hermes or Hermes()
        self.openclaw = openclaw or OpenClaw()
        self.sheriff = sheriff or Sheriff()
        self.sentinel = sentinel or Sentinel()
        self.judge = judge or Judge()

    async def run(self, goal: str) -> dict:
        request = self.rowboat.submit(goal)

        # Planes independientes: paralelos para reducir latencia.
        plan_a, plan_b = await asyncio.gather(
            self.hermes.plan(goal),
            self.openclaw.plan(goal),
        )
        critique_a, critique_b = await asyncio.gather(
            self.hermes.critique(plan_b),
            self.openclaw.critique(plan_a),
        )

        plan = await self.hermes.synthesize(
            goal=goal,
            plan_a=plan_a,
            plan_b=plan_b,
            critique_a=critique_a,
            critique_b=critique_b,
        )
        review = await self.openclaw.review_plan(plan)
        if not review.get("approve"):
            return {"status": "REVISE", "plan": plan, "review": review}

        allowed, reason = self.sheriff.validate(plan)
        if not allowed:
            return {"status": "BLOCK", "reason": reason}

        await self.ruflo.init_swarm()
        tasks = plan.get("tasks", [])
        results = []
        for task in tasks:
            receipt = await self.ruflo.dispatch(task)
            action = self.sentinel.inspect(receipt)
            if action["action"] == "BLOCK":
                return {"status": "BLOCK", "task": task.get("id")}
            if action["action"] in {"RECOVER", "REASSIGN"}:
                return {
                    "status": "REVISE",
                    "task": task.get("id"),
                    "action": action["action"],
                }
            results.append(receipt)

        judgments = []
        for task, evidence in zip(tasks, results):
            ra, rb = await asyncio.gather(
                self.hermes.review(task, evidence),
                self.openclaw.review(task, evidence),
            )
            if ra.get("approve") != rb.get("approve"):
                for _ in range(2):
                    ra, rb = await asyncio.gather(
                        self.hermes.reconsider(task, evidence, rb),
                        self.openclaw.reconsider(task, evidence, ra),
                    )
                    if ra.get("approve") == rb.get("approve"):
                        break

            verdict = self.judge.decide(task, evidence, ra, rb)
            judgments.append({"task": task.get("id"), "verdict": verdict})

        status = "PASS" if judgments and all(
            item["verdict"] == "PASS" for item in judgments
        ) else "REVISE"
        return {
            "status": status,
            "request": request,
            "tasks": judgments,
        }


class EngineeringLoop:
    def __init__(
        self,
        claude=None,
        grok=None,
        meta_team=None,
        mirror_manager=None,
    ) -> None:
        self.claude = claude or ClaudeArquitecto()
        self.reviewer = ClaudeRevisor()
        self.grok = grok or GrokEjecutor()
        self.meta = meta_team or MetaEquipo()
        self.mirrors = mirror_manager

    @staticmethod
    def merge_meta_results(results: list[dict]) -> dict:
        findings = []
        for result in results:
            if result.get("status") != "PASS" or result.get("issues"):
                findings.extend(result.get("issues") or ["meta_review_failed"])
        return {"needs_fix": bool(findings), "findings": findings}

    async def run(self, request: dict) -> dict:
        design = await self.claude.design(
            objective=request["objective"],
            system=request.get("system", ""),
        )
        job = {**request, "design": design, "state": "EXECUTION"}
        result = await self.grok.execute(job)

        for _ in range(3):
            review = await self.reviewer.review(design, result)
            if review.get("status") == "PASS":
                break
            result = await self.grok.correct(job, review)
        else:
            return {"status": "BLOCKED", "stage": "CLAUDE_REVIEW"}

        meta_results = await self.meta.review_parallel(job, result)
        verdict = self.merge_meta_results(meta_results)
        fixed = (
            await self.meta.fixer.correct(job, verdict["findings"])
            if verdict["needs_fix"]
            else result
        )

        validation = await self.meta.review_parallel(job, fixed)
        if not all(item.get("status") == "PASS" for item in validation):
            return {"status": "REVISE", "results": validation}

        return {"status": "PASS", "result": fixed, "validation": validation}
