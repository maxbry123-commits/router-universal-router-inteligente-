"""Utilidades compartidas de las capas. Deterministas, sin LLM. Los motores NO se reescriben: solo se validan y se invocan."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path
from ..contracts import Evidence, LayerResult, Status, canonical, sha256

SKIP = {".git", "node_modules", "__pycache__", "_copias-anteriores"}


def iter_files(root: Path, suffixes: tuple[str, ...]):
    for p in sorted(root.rglob("*"), key=lambda x: x.as_posix()):
        if p.is_file() and p.suffix in suffixes and not (SKIP & set(p.relative_to(root).parts)):
            yield p


def file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def blob_sha(p: Path) -> str:
    data = p.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def file_evidence(p: Path, kind: str) -> Evidence:
    return Evidence(kind=kind, ref=str(p), sha256=file_sha256(p))


def index_evidence(kind: str, root: Path, files: list[Path]) -> Evidence:
    lines = [f"{f.relative_to(root).as_posix()}:{file_sha256(f)}" for f in files]
    return Evidence(kind=kind, ref=str(root), sha256=sha256("\n".join(lines)), detail=f"{len(files)} files")


def result(node, status: Status, *, output=None, evidence=None, gaps=None, touched=None, actions=None) -> LayerResult:
    return LayerResult(node_id=node.node_id, layer=node.layer, status=status, output=output or {},
                       evidence=evidence or [], gaps=gaps or [], touched_paths=touched or [], actions=actions or [])


def missing_inputs(ctx: dict, keys: list[str]) -> list[str]:
    return [k for k in keys if not ctx.get(k)]


def gate_open(node, ctx: dict, gate: str) -> bool:
    return gate in node.authorization and gate in (ctx.get("approvals") or [])


def verify_motor(motor: Path, lock: Path, motor_id: str) -> list[str]:
    """Fail-closed: el blob SHA del motor debe coincidir con MOTOR-CODE-LOCK.json."""
    if not motor.is_file():
        return [f"MOTOR_MISSING:{motor}"]
    if not lock.is_file():
        return [f"MOTOR_LOCK_MISSING:{lock}"]
    entries = [m for m in json.loads(lock.read_text(encoding="utf-8")).get("motors", []) if m.get("id") == motor_id]
    if not entries:
        return [f"MOTOR_NOT_IN_LOCK:{motor_id}"]
    return [] if blob_sha(motor) == entries[0]["canonical_blob_sha"] else [f"MOTOR_CODE_LOCK_GAP:{motor_id}"]


def run_motor(motor: Path, env: dict, timeout_s: float):
    p = subprocess.run([sys.executable, str(motor)], env={**os.environ, **{k: str(v) for k, v in env.items()}},
                       capture_output=True, text=True, timeout=timeout_s)
    report: dict = {}
    try:
        report = json.loads(p.stdout)
    except ValueError:
        for line in reversed((p.stdout or "").splitlines()):
            if line.strip().startswith("{"):
                try:
                    report = json.loads(line)
                    break
                except ValueError:
                    continue
    return p.returncode, report, (p.stdout + p.stderr)[-300:]
