#!/usr/bin/env python3
"""
Prototipo educativo local — Servicio de estados de trabajos.
Sin servidores, sin conexión externa. Python 3 estándar (stdlib).
Funcionalidades: heartbeat, cancelación, historial, validaciones, manejo de errores.
Autor: glm-5.2 — Prueba autorizada por el Director.
"""

import sys
import json
import time
import uuid
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

# ── Enumeración de estados de trabajo ───────────────────────────────

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"

# ── Excepciones personalizadas ──────────────────────────────────────

class JobNotFoundError(Exception):
    """El trabajo solicitado no existe en el servicio."""
    pass

class InvalidStateTransitionError(Exception):
    """Transición de estado no permitida por la máquina de estados."""
    pass

# ── Modelo de trabajo individual ────────────────────────────────────

class Job:
    """Representa un trabajo con pasos, estado e historial de eventos."""

    VALID_TRANSITIONS = {
        JobStatus.PENDING: {JobStatus.RUNNING, JobStatus.CANCELLED},
        JobStatus.RUNNING: {
            JobStatus.PAUSED,
            JobStatus.CANCELLED,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        },
        JobStatus.PAUSED: {JobStatus.RUNNING, JobStatus.CANCELLED},
    }

    TERMINAL = {JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED}

    def __init__(self, name: str, total_steps: int = 10):
        if not name or not isinstance(name, str):
            raise ValueError("El nombre del trabajo no puede estar vacío")
        if not isinstance(total_steps, int) or total_steps <= 0:
            raise ValueError("total_steps debe ser un entero positivo")
        self.id = uuid.uuid4().hex[:12]
        self.name = name.strip()
        self.total_steps = total_steps
        self.current_step = 0
        self.status = JobStatus.PENDING
        self.error_msg: Optional[str] = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_heartbeat = self.created_at
        self.history: list[dict] = []
        self._record("job_created", f"name={self.name}")

    def _record(self, event: str, detail: str = "") -> None:
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "detail": detail,
            "status": self.status.value,
            "step": self.current_step,
        })

    def _check_transition(self, new_status: JobStatus) -> None:
        if self.status in Job.TERMINAL:
            raise InvalidStateTransitionError(
                f"Trabajo {self.id} ya en estado terminal: {self.status.value}"
            )
        allowed = Job.VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed and new_status not in Job.TERMINAL:
            raise InvalidStateTransitionError(
                f"Transición inválida: {self.status.value} → {new_status.value}"
            )

    def start(self) -> None:
        self._check_transition(JobStatus.RUNNING)
        self.status = JobStatus.RUNNING
        self._record("started")

    def heartbeat(self) -> None:
        if self.status != JobStatus.RUNNING:
            raise InvalidStateTransitionError(
                f"Heartbeat inválido: el trabajo está {self.status.value}"
            )
        self.last_heartbeat = datetime.now(timezone.utc).isoformat()
        self._record("heartbeat")

    def advance(self) -> None:
        if self.status != JobStatus.RUNNING:
            raise InvalidStateTransitionError(
                f"advance inválido: el trabajo está {self.status.value}"
            )
        if self.current_step < self.total_steps:
            self.current_step += 1
            self._record("step_advanced", str(self.current_step))
        if self.current_step >= self.total_steps:
            self.status = JobStatus.COMPLETED
            self._record("completed")

    def pause(self) -> None:
        self._check_transition(JobStatus.PAUSED)
        self.status = JobStatus.PAUSED
        self._record("paused")

    def resume(self) -> None:
        self._check_transition(JobStatus.RUNNING)
        self.status = JobStatus.RUNNING
        self._record("resumed")

    def cancel(self) -> None:
        self._check_transition(JobStatus.CANCELLED)
        self.status = JobStatus.CANCELLED
        self._record("cancelled")

    def fail(self, message: str) -> None:
        if not message or not isinstance(message, str):
            raise ValueError("El mensaje de error no puede estar vacío")
        self._check_transition(JobStatus.FAILED)
        self.error_msg = message
        self.status = JobStatus.FAILED
        self._record("failed", message)

    def is_terminal(self) -> bool:
        return self.status in Job.TERMINAL

    def progress_pct(self) -> float:
        if self.total_steps <= 0:
            return 0.0
        return round((self.current_step / self.total_steps) * 100, 1)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "status": self.status.value,
            "error": self.error_msg,
            "progress": self.progress_pct(),
            "created_at": self.created_at,
            "last_heartbeat": self.last_heartbeat,
            "history": self.history,
        }

# ── Servicio gestor de trabajos (thread-safe) ───────────────────────

class JobService:
    """Gestiona la creación, consulta y mutación de trabajos en memoria."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, name: str, total_steps: int = 10) -> dict:
        with self._lock:
            job = Job(name, total_steps)
            self._jobs[job.id] = job
            return job.to_dict()

    def get_job(self, job_id: str) -> dict:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
        return job.to_dict()

    def list_jobs(self) -> list[dict]:
        return [j.to_dict() for j in self._jobs.values()]

    def cancel_job(self, job_id: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
            job.cancel()
            return job.to_dict()

    def pause_job(self, job_id: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
            job.pause()
            return job.to_dict()

    def resume_job(self, job_id: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
            job.resume()
            return job.to_dict()

    def advance_job(self, job_id: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
            job.advance()
            return job.to_dict()

    def heartbeat_job(self, job_id: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
            job.heartbeat()
            return job.to_dict()

    def fail_job(self, job_id: str, message: str) -> dict:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
            job.fail(message)
            return job.to_dict()

    def get_history(self, job_id: str) -> list[dict]:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundError(f"Trabajo no encontrado: {job_id}")
        return job.history

    def clear_all(self) -> int:
        with self._lock:
            count = len(self._jobs)
            self._jobs.clear()
            return count

# ── Demostración local educativa ────────────────────────────────────

def main():
    service = JobService()
    print("=== Servicio de Trabajos — Prototipo Educativo Local ===\n")

    j1 = service.create_job("Procesamiento-A", 5)
    j2 = service.create_job("Procesamiento-B", 8)
    sid1 = j1["id"]
    sid2 = j2["id"]

    service.start(sid1)
    service.start(sid2)

    for _ in range(5):
        service.advance_job(sid1)
        service.heartbeat(sid1)
        time.sleep(0.01)

    for _ in range(3):
        service.advance_job(sid2)
        service.heartbeat(sid2)

    service.pause_job(sid2)
    service.resume_job(sid2)
    service.advance_job(sid2)
    service.fail_job(sid2, "Fallo simulado: memoria insuficiente")

    print("--- Listado de trabajos ---")
    print(json.dumps(service.list_jobs(), indent=2, ensure_ascii=False))

    print("\n--- Historial del trabajo B ---")
    print(json.dumps(service.get_history(sid2), indent=2, ensure_ascii=False))

    print(f"\nTrabajos totales: {len(service.list_jobs())}")

if __name__ == "__main__":
    main()
