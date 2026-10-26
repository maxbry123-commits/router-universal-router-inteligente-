"""Hugging Face Jobs compute adapter for Router Inteligente Universal.

Uses the official huggingface_hub HfApi Jobs API. Jobs are project compute,
not a test-only facility. Authentication comes from HF_TOKEN/environment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from huggingface_hub import HfApi


@dataclass(frozen=True)
class HFJobRequest:
    """Deterministic description of one remote compute job."""

    image: str
    command: Sequence[str]
    flavor: str = "cpu-upgrade"
    timeout: str = "30m"
    env: dict[str, str] = field(default_factory=dict)
    secrets: dict[str, str] = field(default_factory=dict)


@dataclass
class HFJobsCompute:
    """Submit and inspect owned Hugging Face Jobs without exposing secrets."""

    namespace: str = "COMAND-CENTER-1"
    token_env: str = "HF_TOKEN"

    def _api(self) -> HfApi:
        return HfApi()

    def submit(self, request: HFJobRequest) -> dict:
        job = self._api().run_job(
            image=request.image,
            command=list(request.command),
            flavor=request.flavor,
            timeout=request.timeout,
            env=request.env or None,
            secrets=request.secrets or None,
            namespace=self.namespace,
        )
        return {
            "status": "SUBMITTED",
            "job_id": job.id,
            "url": job.url,
            "flavor": request.flavor,
        }

    def inspect(self, job_id: str) -> dict:
        job = self._api().inspect_job(job_id=job_id)
        return {
            "job_id": job.id,
            "url": job.url,
            "stage": job.status.stage,
            "message": job.status.message,
        }
