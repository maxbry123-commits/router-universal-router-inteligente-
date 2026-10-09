"""Elastic HF worker pool controlled by the permanent 16 GB Router.

Policy:
- controller never shuts itself down;
- CPU >= 85% OR RAM >= 85% for 3 samples -> start one worker;
- RAM pressure gets cpu-upgrade (32 GB), CPU-only pressure gets cpu-basic (16 GB);
- temporary workers are cancelled after 300 seconds without assigned traffic;
- child workers never autoscale recursively.

Requires HF_CONTROL_JOBS_TOKEN with Hugging Face Jobs permissions.
"""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any

import httpx

THRESHOLD = float(os.getenv("HF_AUTOSCALE_THRESHOLD", "85"))
IDLE_SECONDS = int(os.getenv("HF_AUTOSCALE_IDLE_SECONDS", "300"))
SAMPLE_SECONDS = int(os.getenv("HF_AUTOSCALE_SAMPLE_SECONDS", "10"))
HOT_SAMPLES = int(os.getenv("HF_AUTOSCALE_HOT_SAMPLES", "3"))
MAX_WORKERS = int(os.getenv("HF_AUTOSCALE_MAX_WORKERS", "4"))
PORT = 8000
CHILD = os.getenv("HF_AUTOSCALE_CHILD", "0") == "1"


@dataclass
class Worker:
    job_id: str
    url: str
    flavor: str
    created_at: float
    last_used_at: float
    state: str = "starting"

    def public(self) -> dict[str, Any]:
        now = time.time()
        out = asdict(self)
        out["age_s"] = round(now - self.created_at, 1)
        out["idle_s"] = round(now - self.last_used_at, 1)
        return out


class HFWorkerPool:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workers: dict[str, Worker] = {}
        self._rr = 0
        self._hot = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.cpu_percent = 0.0
        self.ram_percent = 0.0
        self.last_error: str | None = None
        self.last_scale_reason: str | None = None

    @property
    def hf_token(self) -> str:
        return os.getenv("HF_CONTROL_JOBS_TOKEN", "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.hf_token) and not CHILD

    def _api(self):
        from huggingface_hub import HfApi
        if not self.hf_token:
            raise RuntimeError("HF_CONTROL_JOBS_TOKEN ausente")
        return HfApi(token=self.hf_token)

    def _metrics(self) -> tuple[float, float]:
        import psutil
        return float(psutil.cpu_percent(interval=0.2)), float(psutil.virtual_memory().percent)

    def _command(self) -> str:
        repo = "https://github.com/maxbry123-commits/router-universal-router-inteligente-"
        return (
            "set -e; "
            "git clone --depth 1 " + repo + " /tmp/riu && "
            "cd '/tmp/riu/router inteligente universal' && "
            "pip install -q fastapi 'uvicorn[standard]' pydantic huggingface_hub "
            "cryptography pyyaml requests httpx psutil && "
            "uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port 8000"
        )

    def _forwarded_secrets(self) -> dict[str, str]:
        names = [
            "HF_CONTROL_JOBS_TOKEN", "HF_TOKEN", "HF_WRITE_TOKEN",
            "GITHUB_TOKEN", "GITHUB_TOKEN_1", "GITHUB_TOKEN_2", "GITHUB_TOKEN_3", "RIU_GITHUB_TOKEN", "RIU_GITHUB_ACCOUNTS",
            "RIU_ROUTER_API_KEY", "RIU_AGENT_API_KEYS",
            "RIU_DEEPSEEK_HARNESS_URL", "RIU_DEEPSEEK_HARNESS_API_KEY", "RIU_DEEPSEEK_HARNESS_PATH",
            "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4",
            "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4",
            "GROQ_API_KEY_5", "GROQ_API_KEY_6", "GROQ_API_KEY_7",
            *[f"OPENAI_API_KEY_{i}" for i in range(1, 15)],
        ]
        return {name: os.environ[name] for name in names if os.getenv(name)}

    def launch(self, flavor: str, reason: str) -> Worker:
        if not self.enabled:
            raise RuntimeError("autoscaler deshabilitado")
        with self._lock:
            live = [w for w in self._workers.values() if w.state in {"starting", "running"}]
            if len(live) >= MAX_WORKERS:
                raise RuntimeError("max workers reached")

        job = self._api().run_job(
            image="python:3.12",
            command=["bash", "-lc", self._command()],
            flavor=flavor,
            timeout=os.getenv("HF_AUTOSCALE_WORKER_TIMEOUT", "12h"),
            expose=[PORT],
            secrets=self._forwarded_secrets(),
            env={"HF_AUTOSCALE_CHILD": "1"},
        )
        now = time.time()
        worker = Worker(
            job_id=job.id,
            url=f"https://{job.id}--{PORT}.hf.jobs",
            flavor=flavor,
            created_at=now,
            last_used_at=now,
        )
        with self._lock:
            self._workers[worker.job_id] = worker
            self.last_scale_reason = reason
        return worker

    def inspect(self) -> None:
        if not self.hf_token:
            return
        api = self._api()
        with self._lock:
            ids = list(self._workers)
        for job_id in ids:
            try:
                info = api.inspect_job(job_id=job_id)
                stage = str(getattr(info.status, "stage", "") or "").upper()
                with self._lock:
                    worker = self._workers.get(job_id)
                    if not worker:
                        continue
                    if stage == "RUNNING":
                        worker.state = "running"
                    elif stage in {"COMPLETED", "CANCELED", "ERROR", "DELETED"}:
                        worker.state = stage.lower()
            except Exception as exc:
                self.last_error = f"inspect:{type(exc).__name__}:{str(exc)[:120]}"

    def reap_idle(self) -> list[str]:
        if not self.hf_token:
            return []
        now = time.time()
        with self._lock:
            candidates = [
                w for w in self._workers.values()
                if w.state in {"starting", "running"} and now - w.last_used_at >= IDLE_SECONDS
            ]
        cancelled: list[str] = []
        api = self._api()
        for worker in candidates:
            try:
                api.cancel_job(job_id=worker.job_id)
                with self._lock:
                    worker.state = "canceled"
                cancelled.append(worker.job_id)
            except Exception as exc:
                self.last_error = f"reap:{type(exc).__name__}:{str(exc)[:120]}"
        return cancelled

    def choose(self) -> Worker | None:
        with self._lock:
            live = [w for w in self._workers.values() if w.state == "running"]
            if not live:
                return None
            worker = live[self._rr % len(live)]
            self._rr += 1
            worker.last_used_at = time.time()
            return worker

    async def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        worker = self.choose()
        if worker is None:
            worker = self.launch("cpu-basic", "first managed request")
            return {"status": "starting", "worker": worker.public(), "retry_after_s": 10}

        key = os.getenv("RIU_ROUTER_API_KEY", "")
        headers = {"X-API-Key": key} if key else {}
        target = worker.url.rstrip("/") + os.getenv("HF_AUTOSCALE_WORKER_INVOKE_PATH", "/chat/send")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(target, json=payload, headers=headers)
        worker.last_used_at = time.time()
        if response.status_code >= 400:
            return {"status": "degraded", "http_status": response.status_code, "body": response.text[:1000]}
        try:
            body: Any = response.json()
        except ValueError:
            body = {"text": response.text}
        return {"status": "ok", "worker": worker.job_id, "result": body}

    def status(self) -> dict[str, Any]:
        try:
            self.cpu_percent, self.ram_percent = self._metrics()
        except Exception as exc:
            self.last_error = f"metrics:{type(exc).__name__}:{str(exc)[:120]}"
        with self._lock:
            workers = [w.public() for w in self._workers.values()]
        return {
            "role": "permanent-controller",
            "enabled": self.enabled,
            "child": CHILD,
            "threshold_percent": THRESHOLD,
            "idle_seconds": IDLE_SECONDS,
            "cpu_percent": self.cpu_percent,
            "ram_percent": self.ram_percent,
            "workers": workers,
            "max_workers": MAX_WORKERS,
            "jobs_token_present": bool(self.hf_token),
            "last_scale_reason": self.last_scale_reason,
            "last_error": self.last_error,
        }

    def _loop(self) -> None:
        while not self._stop.wait(max(SAMPLE_SECONDS, 5)):
            try:
                self.cpu_percent, self.ram_percent = self._metrics()
                self.inspect()
                self.reap_idle()

                hot = self.cpu_percent >= THRESHOLD or self.ram_percent >= THRESHOLD
                self._hot = self._hot + 1 if hot else 0
                if self.enabled and self._hot >= HOT_SAMPLES:
                    flavor = "cpu-upgrade" if self.ram_percent >= THRESHOLD else "cpu-basic"
                    reason = (
                        f"cpu={self.cpu_percent:.1f}% "
                        f"ram={self.ram_percent:.1f}% "
                        f"threshold={THRESHOLD:.1f}%"
                    )
                    try:
                        self.launch(flavor, reason)
                    except RuntimeError:
                        pass
                    self._hot = 0
            except Exception as exc:
                self.last_error = f"loop:{type(exc).__name__}:{str(exc)[:120]}"

    def start(self) -> None:
        if CHILD or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name="hf-worker-pool")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()


POOL = HFWorkerPool()
