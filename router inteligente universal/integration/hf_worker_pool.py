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
MAX_WORKERS = int(os.getenv("HF_AUTOSCALE_MAX_WORKERS", "10"))
PORT = 8000
CHILD = os.getenv("HF_AUTOSCALE_CHILD", "0") == "1"


WARMUP_SECONDS = int(os.getenv("HF_AUTOSCALE_WARMUP_SECONDS", "180"))  # no scaling while the Router itself boots


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip()


CORES_POR_FLAVOR = {"cpu-basic": 2.0, "cpu-upgrade": 8.0}


def _cpu_limit() -> float:
    """Nucleos PAGADOS del procesador (cpu-basic=2, cpu-upgrade=8). HF deja ver y usar nucleos de mas (cpu.max=max y
    afinidad de toda la maquina), asi que contar esos dejaba la CPU en ~30 % aunque el Router estuviera lleno."""
    env = os.getenv("RIU_CPU_CORES") or CORES_POR_FLAVOR.get(os.getenv("RIU_FLAVOR", ""), 0)
    if env:
        return float(env)
    try:
        quota, period = _read("/sys/fs/cgroup/cpu.max").split()[:2]
        if quota != "max":
            return max(0.1, int(quota) / int(period))
    except Exception:  # noqa: BLE001
        pass
    return 2.0  # cpu-basic, el procesador fijo del Router


def _cgroup_usage_s() -> float:
    for line in _read("/sys/fs/cgroup/cpu.stat").splitlines():
        if line.startswith("usage_usec "):
            return int(line.split()[1]) / 1e6
    raise RuntimeError("no usage_usec")


def _tree_cpu_s() -> float:
    import psutil

    me = psutil.Process()
    total = 0.0
    for p in [me, *me.children(recursive=True)]:
        try:
            t = p.cpu_times()
            total += t.user + t.system
        except Exception:  # noqa: BLE001
            pass
    return total


def _container_cpu_percent(window: float) -> tuple[float, str]:
    limit = _cpu_limit()
    for name, reader in (("cgroup", _cgroup_usage_s), ("proceso", _tree_cpu_s)):
        try:
            u0, t0 = reader(), time.monotonic()
            time.sleep(window)
            u1, t1 = reader(), time.monotonic()
            return min(100.0, max(0.0, 100.0 * (u1 - u0) / ((t1 - t0) * limit))), name
        except Exception:  # noqa: BLE001
            continue
    import psutil

    return float(psutil.cpu_percent(interval=window)), "host"


def _container_ram_percent() -> tuple[float, str]:
    try:
        limit = _read("/sys/fs/cgroup/memory.max")
        if limit != "max":
            return 100.0 * int(_read("/sys/fs/cgroup/memory.current")) / int(limit), "cgroup"
    except Exception:  # noqa: BLE001
        pass
    import psutil

    return float(psutil.virtual_memory().percent), "host"


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
        self.metrics_source = ""
        self.started_at = time.time()

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
        """CPU and RAM of THIS container (cgroup), not of the HF host machine.

        psutil.cpu_percent() sees the whole shared host (always ~100% on HF Jobs), which made the pool start a worker
        every 30 s with no traffic (Director audit 2026-10-03). Order: cgroup v2 -> own process tree -> psutil host."""
        cpu = _container_cpu_percent(1.0)
        ram = _container_ram_percent()
        self.metrics_source = f"cpu:{cpu[1]} ram:{ram[1]}"
        return cpu[0], ram[0]

    def _command(self) -> list[str]:
        from .hf_runtime import bootstrap_command

        return bootstrap_command(PORT)  # code from the HF bucket bundle: no GitHub clone, no GitHub token in the worker

    def _forwarded_secrets(self) -> dict[str, str]:
        from .hf_runtime import forwarded_secrets

        out = forwarded_secrets()
        if "HF_TOKEN" not in out and self.hf_token:
            out["HF_TOKEN"] = self.hf_token  # the worker needs it to fetch the bundle and to be reached through hf.jobs
        return out

    def _headers(self) -> dict[str, str]:
        """hf.jobs proxy wants an HF token (Authorization); the Router behind it wants its own key (X-API-Key)."""
        headers = {"Authorization": "Bearer " + self.hf_token} if self.hf_token else {}
        key = os.getenv("RIU_ROUTER_API_KEY", "")
        if key:
            headers["X-API-Key"] = key
        return headers

    def offload_target(self) -> "Worker | None":
        """A running worker while this Router is hot (>= THRESHOLD): the OpenAI door forwards the request there."""
        if CHILD or not (self.cpu_percent >= THRESHOLD or self.ram_percent >= THRESHOLD):
            return None
        return self.choose()

    def launch(self, flavor: str, reason: str) -> Worker:
        if not self.enabled:
            raise RuntimeError("autoscaler deshabilitado")
        with self._lock:
            live = [w for w in self._workers.values() if w.state in {"starting", "running"}]
            if len(live) >= MAX_WORKERS:
                raise RuntimeError("max workers reached")

        job = self._api().run_job(namespace=os.getenv("RIU_HF_NAMESPACE", "COMAND-CENTER-1"), 
            image="python:3.12",
            command=self._command(),
            flavor=flavor,
            timeout=os.getenv("HF_AUTOSCALE_WORKER_TIMEOUT", "12h"),
            expose=[PORT],
            secrets=self._forwarded_secrets(),
            env={"HF_AUTOSCALE_CHILD": "1", "RIU_DATA_DIR": "/tmp/riu", "RIU_VAULT_PATH": "/tmp/riu/riu_vault.db",
                 "RIU_VAULT_SOURCE": os.getenv("RIU_VAULT_SOURCE", ""), "RIU_CODE_BUNDLE": os.getenv("RIU_CODE_BUNDLE", ""),
                 "RIU_VAULT_PROVIDERS_SOURCE": os.getenv("RIU_VAULT_PROVIDERS_SOURCE", ""), "RIU_ROOT": os.getenv("RIU_ROOT", ""),
                 "HF_BUCKET_ID": os.getenv("HF_BUCKET_ID", "")},
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
                info = api.inspect_job(namespace=os.getenv("RIU_HF_NAMESPACE", "COMAND-CENTER-1"), job_id=job_id)
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
                api.cancel_job(namespace=os.getenv("RIU_HF_NAMESPACE", "COMAND-CENTER-1"), job_id=worker.job_id)
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

        headers = self._headers()
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
            "metrics_source": self.metrics_source,
            "warmup_seconds": WARMUP_SECONDS,
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
                warm = time.time() - self.started_at >= WARMUP_SECONDS
                if self.enabled and warm and self._hot >= HOT_SAMPLES:
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
        self.started_at = time.time()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="hf-worker-pool")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()


POOL = HFWorkerPool()
