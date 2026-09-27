"""MirrorManager — worktree mirrors selectivos (doc 22).

Mirror = entorno de trabajo aislado (git worktree), no una copia de la
arquitectura. Al terminar: DIFF -> TEST -> SHERIFF -> MERGE SELECTIVO -> MAIN.
Si falla: keep_for_debug() y main queda intacto.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

SYSTEM_MAP = {
    "factory-ui": {"paths": ["Frontend/factory-v0/", "tests/factory/", "contracts/ui/"]},
    "router": {"paths": ["router/", "integration/", "tests/router/"]},
    "memory": {"paths": ["memory/", "tests/memory/"]},
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

    def _mirror_git(self, job_id: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.mirrors[job_id]["workspace"],
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

    def _changed_files(self, job_id: str) -> list[str]:
        """Incluye modificados, borrados y NUEVOS no rastreados."""
        proc = self._mirror_git(job_id, "status", "--porcelain", "--untracked-files=all")
        files: list[str] = []
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1].strip()
            files.append(path)
        return files

    def diff(self, job_id: str) -> str:
        """Diff del mirror, incluyendo una lista explícita de no rastreados."""
        tracked = self._mirror_git(job_id, "diff", "HEAD").stdout
        untracked = self._mirror_git(
            job_id, "ls-files", "--others", "--exclude-standard"
        ).stdout
        if untracked.strip():
            tracked += "\n# UNTRACKED\n" + untracked
        return tracked

    @staticmethod
    def _is_allowed(path: str, allowed_paths: list[str]) -> bool:
        clean = path.replace("\\", "/").lstrip("./")
        return any(
            clean == root.rstrip("/") or clean.startswith(root)
            for root in allowed_paths
        )

    def merge_selectivo(self, job_id: str, sheriff) -> tuple[bool, str]:
        """Solo fusiona cambios declarados y aprobados por el Sheriff."""
        mirror = self.mirrors[job_id]
        archivos = self._changed_files(job_id)
        if not archivos:
            return False, "Sin cambios para fusionar"

        fuera = [p for p in archivos if not self._is_allowed(p, mirror["allowed_paths"])]
        if fuera:
            return False, f"Ruta prohibida o fuera de alcance: {fuera[0]}"

        plan = {
            "tasks": [{
                "id": job_id,
                "acceptance": ["diff aprobado por sheriff"],
                "allowed_paths": archivos,
            }]
        }
        ok, motivo = sheriff.validate(plan)
        if not ok:
            return False, motivo

        self._mirror_git(job_id, "add", "-A")
        self._mirror_git(
            job_id,
            "-c", "user.email=mirror@yaiwes",
            "-c", "user.name=mirror",
            "commit", "-m", f"mirror {job_id}",
        )

        # merge --no-ff crea otro commit; la identidad debe existir también aquí.
        self._git(
            "-c", "user.email=mirror@yaiwes",
            "-c", "user.name=mirror",
            "merge", "--no-ff", "--no-edit", f"mirror/{job_id}",
        )
        self._git("worktree", "remove", mirror["workspace"], "--force")
        return True, "MERGED"

    def keep_for_debug(self, job_id: str) -> dict:
        """Conserva el mirror para depuración; main queda intacto."""
        mirror = self.mirrors[job_id]
        mirror["debug"] = True
        return mirror
