"""MirrorManager — worktree mirrors selectivos (doc 22).

Mirror = entorno de trabajo aislado (git worktree), no una copia de la
arquitectura. Al terminar: DIFF -> TEST -> SHERIFF -> MERGE SELECTIVO -> MAIN.
Si falla: keep_for_debug() y main queda intacto.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

SYSTEM_MAP = {
    "factory-ui": {
        "paths": [
            "Frontend/factory-v0/",
            "tests/factory/",
            "contracts/ui/",
        ]
    },
    "router": {
        "paths": [
            "router/",
            "integration/",
            "tests/router/",
        ]
    },
    "memory": {
        "paths": [
            "memory/",
            "tests/memory/",
        ]
    },
}


class MirrorManager:
    """Crea y gobierna mirrors (worktrees) por job."""

    def __init__(self, repo_dir: str | Path) -> None:
        self.repo_dir = Path(repo_dir)
        self.mirrors: dict[str, dict] = {}

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    def create(self, job_id: str, system: str) -> dict:
        if system not in SYSTEM_MAP:
            raise ValueError(f"Sistema desconocido: {system}")

        paths = SYSTEM_MAP[system]["paths"]
        mirror_dir = self.repo_dir.parent / "mirrors" / job_id
        mirror_dir.parent.mkdir(parents=True, exist_ok=True)

        self._git("worktree", "add", str(mirror_dir), "-b", f"mirror/{job_id}")

        mirror = {
            "job_id": job_id,
            "workspace": str(mirror_dir),
            "allowed_paths": paths,
        }
        self.mirrors[job_id] = mirror
        return mirror

    def diff(self, job_id: str) -> str:
        """Diff del mirror contra su punto de partida (rama mirror/<job>)."""
        mirror = self.mirrors[job_id]
        proc = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=mirror["workspace"],
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout

    def merge_selectivo(self, job_id: str, sheriff) -> tuple[bool, str]:
        """Solo fusiona si el Sheriff aprueba las rutas tocadas."""
        mirror = self.mirrors[job_id]
        proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=mirror["workspace"],
            capture_output=True,
            text=True,
            check=True,
        )
        archivos = [l for l in proc.stdout.splitlines() if l.strip()]

        plan = {
            "tasks": [
                {
                    "id": job_id,
                    "acceptance": ["diff aprobado por sheriff"],
                    "allowed_paths": archivos or mirror["allowed_paths"],
                }
            ]
        }
        ok, motivo = sheriff.validate(plan)
        if not ok:
            return False, motivo

        # commit en el mirror y merge de la rama en main
        subprocess.run(
            ["git", "add", "-A"], cwd=mirror["workspace"],
            capture_output=True, text=True, check=True,
        )
        subprocess.run(
            ["git", "-c", "user.email=mirror@yaiwes", "-c", "user.name=mirror",
             "commit", "-m", f"mirror {job_id}", "--allow-empty"],
            cwd=mirror["workspace"], capture_output=True, text=True, check=True,
        )
        self._git("merge", "--no-ff", f"mirror/{job_id}")
        self._git("worktree", "remove", mirror["workspace"], "--force")
        return True, "MERGED"

    def keep_for_debug(self, job_id: str) -> dict:
        """Conserva el mirror para depuración; main queda intacto."""
        mirror = self.mirrors[job_id]
        mirror["debug"] = True
        return mirror
