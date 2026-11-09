"""Sheriff duro: solo máquina HF con 32 GB RAM antes de run_job.

Orden Director: procesador/máquina de 32 GB RAM; cualquier otra → FAIL y no lanzar.
Los IDs técnicos de flavor HF son detalle de implementación (no texto del Director).
"""
from __future__ import annotations

from typing import Any, Mapping

# Capacidad RAM (GB) conocida por flavor técnico HF Jobs (docs HF).
_FLAVOR_RAM_GB: dict[str, int] = {
    "cpu-basic": 16,
    "cpu-upgrade": 32,
    "t4-small": 16,
    "t4-medium": 32,
    "a10g-small": 24,
    "a10g-large": 48,
    "a100-large": 80,
}

ALLOWED_RAM_GB = 32


class HardwareSheriffError(RuntimeError):
    """La máquina pedida no es la de 32 GB RAM."""


def ram_gb_for_flavor(flavor: str | None) -> int | None:
    if not flavor:
        return None
    return _FLAVOR_RAM_GB.get(str(flavor).strip().lower())


def assert_machine_32gb_ram(*, flavor: str | None = None, ram_gb: int | None = None) -> None:
    """FAIL cerrado si la máquina no es 32 GB RAM."""
    gb = ram_gb if ram_gb is not None else ram_gb_for_flavor(flavor)
    label = f"flavor={flavor!r}" if flavor else f"ram_gb={ram_gb!r}"
    if gb is None:
        raise HardwareSheriffError(
            f"SHERIFF FAIL: máquina desconocida ({label}); solo se permite 32 GB RAM. No lanzar."
        )
    if gb != ALLOWED_RAM_GB:
        raise HardwareSheriffError(
            f"SHERIFF FAIL: máquina {label} tiene {gb} GB RAM; obligatorio {ALLOWED_RAM_GB} GB. No lanzar."
        )


def guarded_run_job(api: Any, **kwargs: Any) -> Any:
    """Envuelve api.run_job: valida máquina 32 GB RAM y luego lanza."""
    flavor = kwargs.get("flavor") or kwargs.get("hardware_flavor")
    assert_machine_32gb_ram(flavor=flavor)
    return api.run_job(**kwargs)


def job_is_allowed_32gb(job: Any) -> bool:
    """True si un Job ya existente declara máquina 32 GB RAM."""
    flavor = None
    for attr in ("flavor", "hardware", "machine_type"):
        flavor = getattr(job, attr, None) or flavor
    if isinstance(job, Mapping):
        flavor = job.get("flavor") or job.get("hardware") or flavor
        compute = job.get("compute") or {}
        if isinstance(compute, Mapping):
            flavor = compute.get("flavor") or flavor
    gb = ram_gb_for_flavor(str(flavor) if flavor else None)
    return gb == ALLOWED_RAM_GB
