"""I3 — Cola de tareas + vigilante de autoescalado (diseño ejecutable).

Reglas del plan:
  - procesadores 16 GB: se disparan al 80 % de uso, tope 3.
  - cadena 32 GB (agentes y modelos locales): siguiente al 85 %, tope 10.
  - un worker se apaga solo tras 15 min sin tareas y se da de baja del registro.

La cola y el registro viven en JSON (RIU_COLA_DIR, por defecto <repo>/chat router/EVIDENCIA/cola) para que el
Router, los agentes y el panel vean el mismo estado. El lanzador es intercambiable: `LanzadorLocal` (proceso en
la misma máquina, para el banco de pruebas) y `LanzadorHFJob` (Job de Hugging Face, cuando el Director autorice
la máquina de pago). El vigilante no inventa métricas: lee /proc y, si no puede, marca GAP.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

DIR = Path(os.getenv("RIU_COLA_DIR") or Path(__file__).resolve().parents[1] / "EVIDENCIA" / "cola")
TAREAS = DIR / "tareas.json"
WORKERS = DIR / "workers.json"

UMBRAL_16 = 0.80
UMBRAL_32 = 0.85
TOPE_16 = 3
TOPE_32 = 10
INACTIVIDAD_S = 15 * 60


@dataclass
class Tarea:
    id: str
    orden: str
    clase: str = "16gb"  # 16gb = tarea normal; 32gb = agentes / modelos locales
    estado: str = "pendiente"  # pendiente | en_curso | hecha | fallida
    worker: str | None = None
    creada: float = field(default_factory=time.time)
    actualizada: float = field(default_factory=time.time)
    resultado: dict[str, Any] | None = None


@dataclass
class Worker:
    id: str
    clase: str
    pid: int | None
    arrancado: float
    ultima_tarea: float


def _leer(path: Path, defecto: Any) -> Any:
    if not path.exists():
        return defecto
    return json.loads(path.read_text(encoding="utf-8") or "null") or defecto


def _escribir(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ----------------------------- cola -----------------------------
def encolar(orden: str, clase: str = "16gb") -> Tarea:
    t = Tarea(id=uuid.uuid4().hex[:12], orden=orden, clase=clase)
    tareas = _leer(TAREAS, [])
    tareas.append(asdict(t))
    _escribir(TAREAS, tareas)
    return t


def tomar(worker_id: str, clase: str | None = None) -> Tarea | None:
    tareas = _leer(TAREAS, [])
    for row in tareas:
        if row["estado"] == "pendiente" and (clase is None or row["clase"] == clase):
            row.update(estado="en_curso", worker=worker_id, actualizada=time.time())
            _escribir(TAREAS, tareas)
            return Tarea(**row)
    return None


def cerrar(tarea_id: str, resultado: dict[str, Any], ok: bool = True) -> None:
    tareas = _leer(TAREAS, [])
    for row in tareas:
        if row["id"] == tarea_id:
            row.update(estado="hecha" if ok else "fallida", resultado=resultado, actualizada=time.time())
    _escribir(TAREAS, tareas)


def pendientes(clase: str | None = None) -> list[Tarea]:
    return [Tarea(**r) for r in _leer(TAREAS, [])
            if r["estado"] == "pendiente" and (clase is None or r["clase"] == clase)]


# ----------------------------- métricas -----------------------------
def uso() -> dict[str, float]:
    """Uso real de CPU (1 s de muestreo) y RAM a partir de /proc. Sin dependencias externas."""
    def _cpu_snapshot() -> tuple[int, int]:
        parts = [int(x) for x in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
        return sum(parts), parts[3]

    total0, idle0 = _cpu_snapshot()
    time.sleep(1.0)
    total1, idle1 = _cpu_snapshot()
    cpu = 1.0 - (idle1 - idle0) / max(total1 - total0, 1)
    mem = {k.split(":")[0]: int(k.split()[1]) for k in Path("/proc/meminfo").read_text().splitlines()[:5]}
    ram = 1.0 - mem.get("MemAvailable", 0) / max(mem.get("MemTotal", 1), 1)
    return {"cpu": round(cpu, 3), "ram": round(ram, 3)}


# ----------------------------- lanzadores -----------------------------
class Lanzador(Protocol):
    def lanzar(self, clase: str) -> Worker: ...
    def apagar(self, worker: Worker) -> None: ...


class LanzadorLocal:
    """Banco de pruebas: el worker es un proceso `worker.py` en esta misma máquina."""

    def lanzar(self, clase: str) -> Worker:
        script = Path(__file__).resolve().parent / "worker.py"
        proc = subprocess.Popen(["python3", str(script), "--clase", clase],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return Worker(id=f"local-{proc.pid}", clase=clase, pid=proc.pid, arrancado=time.time(), ultima_tarea=time.time())

    def apagar(self, worker: Worker) -> None:
        if worker.pid:
            try:
                os.kill(worker.pid, 15)
            except ProcessLookupError:
                pass


class LanzadorHFJob:
    """Producción: cada worker es un Job de Hugging Face. Requiere HF_TOKEN y autorización de gasto del Director."""

    def __init__(self, flavor_16: str = "cpu-basic", flavor_32: str = "cpu-upgrade") -> None:
        self.flavors = {"16gb": flavor_16, "32gb": flavor_32}

    def lanzar(self, clase: str) -> Worker:
        token = os.getenv("HF_TOKEN") or os.getenv("HF_TOKEN_1")
        if not token:
            raise RuntimeError("GAP: sin HF_TOKEN; el Director aún no autorizó la máquina de pago")
        from huggingface_hub import run_job  # import tardío: solo en producción

        job = run_job(image=os.getenv("RIU_WORKER_IMAGE", "python:3.11"), flavor=self.flavors[clase],
                      command=["bash", "-lc", os.getenv("RIU_WORKER_CMD", "python -m riu_worker")], token=token)
        return Worker(id=job.id, clase=clase, pid=None, arrancado=time.time(), ultima_tarea=time.time())

    def apagar(self, worker: Worker) -> None:
        from huggingface_hub import HfApi

        HfApi(token=os.getenv("HF_TOKEN") or os.getenv("HF_TOKEN_1")).cancel_job(worker.id)


# ----------------------------- vigilante -----------------------------
def registro() -> list[Worker]:
    return [Worker(**w) for w in _leer(WORKERS, [])]


def guardar_registro(ws: list[Worker]) -> None:
    _escribir(WORKERS, [asdict(w) for w in ws])


def vigilar(lanzador: Lanzador, *, ahora: float | None = None, metricas: dict[str, float] | None = None) -> dict[str, Any]:
    """Una vuelta del vigilante: enciende lo necesario y apaga lo inactivo. Devuelve lo que hizo."""
    ahora = ahora or time.time()
    m = metricas or uso()
    carga = max(m["cpu"], m["ram"])
    ws = registro()
    encendidos: list[str] = []
    apagados: list[str] = []

    n16 = sum(1 for w in ws if w.clase == "16gb")
    n32 = sum(1 for w in ws if w.clase == "32gb")
    if pendientes("32gb") and carga >= UMBRAL_32 and n32 < TOPE_32:
        w = lanzador.lanzar("32gb")
        ws.append(w)
        encendidos.append(w.id)
    elif pendientes("16gb") and carga >= UMBRAL_16 and n16 < TOPE_16:
        w = lanzador.lanzar("16gb")
        ws.append(w)
        encendidos.append(w.id)

    vivos: list[Worker] = []
    for w in ws:
        if ahora - w.ultima_tarea > INACTIVIDAD_S:
            lanzador.apagar(w)
            apagados.append(w.id)
        else:
            vivos.append(w)
    guardar_registro(vivos)
    return {"uso": m, "pendientes": len(pendientes()), "workers": len(vivos),
            "encendidos": encendidos, "apagados": apagados}
