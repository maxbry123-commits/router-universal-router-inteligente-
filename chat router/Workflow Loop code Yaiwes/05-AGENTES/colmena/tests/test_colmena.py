"""T02: pruebas sin red de YaiwesHive y EngineeringLoop."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

os.environ["SIMULADO"] = "1"
sys.path.insert(0, str(Path(__file__).parents[1]))

from agentes import Hermes, OpenClaw  # noqa: E402
from colmena import EngineeringLoop, YaiwesHive  # noqa: E402


class RejectPlan(OpenClaw):
    async def review_plan(self, plan):
        return {"approve": False, "issues": ["revisar"]}


class BadPlan(Hermes):
    async def synthesize(self, **payload):
        return {
            "tasks": [{
                "id": "bad",
                "objective": "sin acceptance",
                "role": "coder",
                "allowed_paths": ["src/"],
            }]
        }


def test_hive_pass():
    result = asyncio.run(YaiwesHive().run("objetivo"))
    assert result["status"] == "PASS"
    assert result["tasks"] == [{"task": "task-1", "verdict": "PASS"}]


def test_hive_revise_por_debate():
    result = asyncio.run(YaiwesHive(openclaw=RejectPlan()).run("objetivo"))
    assert result["status"] == "REVISE"
    assert result["review"]["approve"] is False


def test_hive_block_por_sheriff():
    result = asyncio.run(YaiwesHive(hermes=BadPlan()).run("objetivo"))
    assert result["status"] == "BLOCK"
    assert "aceptación" in result["reason"]


def test_engineering_loop_pass_meta_paralelo():
    result = asyncio.run(EngineeringLoop().run({
        "job_id": "J1",
        "objective": "implementar",
        "system": "chat",
    }))
    assert result["status"] == "PASS"
    assert len(result["validation"]) == 4
