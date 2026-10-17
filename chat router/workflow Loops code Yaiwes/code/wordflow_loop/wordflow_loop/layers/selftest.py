"""Autoprueba de las capas L01-L06 sobre LayerRunner. Uso (desde wordflow_loop/): python -m wordflow_loop.layers.selftest
Fase B (opcional): MOTOR3=<ruta motor 3> MOTOR_LOCK=<ruta MOTOR-CODE-LOCK.json> para copiar de verdad con el motor 3."""
from __future__ import annotations
import json, os, sys, tempfile
from pathlib import Path
from ..contracts import NodeContract, Status
from ..runner import LayerRunner
from . import execute

G4, G5 = "DIRECTOR_APPROVAL_REQUIRED", "SOURCE_LOCK_AND_DIRECTOR_APPROVAL"


def _n(nid, layer, deps=(), mutation=False, auth=(), paths=(), acts=("read",)):
    return NodeContract.build(node_id=nid, layer=layer, literal=nid, depends_on=tuple(deps), mutation=mutation,
                              authorization=tuple(auth), allowed_paths=tuple(paths), allowed_actions=tuple(acts))


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    repo, src, dst = tmp / "repo", tmp / "src", tmp / "dst"
    for d in (repo, src, dst):
        d.mkdir()
    (repo / "a.md").write_text("# doc\n"); (repo / "b.json").write_text("{\"k\": 1}")
    (repo / "c.py").write_text("x = 1\n"); (repo / "d.yaml").write_text("k: v\n")
    for i in range(3):
        (src / f"f{i}.txt").write_text(f"file {i}\n")
    mb, ma = tmp / "before.json", tmp / "after.json"
    mb.write_text(json.dumps({"a": "1", "b": "2"})); ma.write_text(json.dumps({"a": "1", "b": "3", "c": "4"}))
    ctx = {"research_sources": [str(repo)], "repo_root": str(repo), "manifest_before": str(mb), "manifest_after": str(ma)}
    nodes = [_n("n1", "L01_RESEARCH"), _n("n2", "L02_XRAY_DOCUMENTS", ["n1"]), _n("n3", "L03_XRAY_CODE", ["n1"]),
             _n("n4", "L04_COPY_MOVE", ["n2", "n3"], True, [G4], [str(dst)], ("copy",)),
             _n("n5", "L05_DOWNLOAD_EXTRACT", ["n3"], True, [G5], [str(dst)], ("download", "extract")),
             _n("n6", "L06_SOURCE_EVOLUTION", ["n2", "n3"])]
    fails = []
    print("== Fase A: sin aprobacion ni motores (deben cerrar solo L01,L02,L03,L06)")
    res = LayerRunner(execute).run(nodes, dict(ctx))
    for k, r in res.items():
        print(f"  {k} {r.layer}: {r.status.value} {r.gaps[:1]}")
    for k in ("n1", "n2", "n3", "n6"):
        if res[k].status != Status.PASS:
            fails.append(f"A:{k}")
    for k in ("n4", "n5"):
        if res[k].status == Status.PASS:
            fails.append(f"A:{k}_paso_sin_aprobacion")
    m3, lock = os.getenv("MOTOR3"), os.getenv("MOTOR_LOCK")
    if m3 and lock:
        print("== Fase B: L04 real con motor 3 (SHA validado) y aprobacion")
        ctx2 = {**ctx, "approvals": [G4], "motor_3_path": m3, "motor_lock": lock, "source_dir": str(src),
                "dest_dir": str(dst), "state_file": str(tmp / "state.json"), "batch_size": 2}
        r2 = LayerRunner(execute).run(nodes[:5], ctx2)["n4"]
        copied = sorted(p.name for p in dst.glob("*.txt"))
        print(f"  n4: {r2.status.value} copiados={copied} gaps={r2.gaps[:1]}")
        if r2.status != Status.PASS or len(copied) != 3:
            fails.append("B:n4")
    print("RESULTADO:", "OK" if not fails else f"FALLA {fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
