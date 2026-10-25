from __future__ import annotations
from pathlib import Path
from ..contracts import Evidence, Status, sha256
from ._common import gate_open, missing_inputs, result, run_motor, verify_motor

LAYER = "L05_DOWNLOAD_EXTRACT"
GATE = "SOURCE_LOCK_AND_DIRECTOR_APPROVAL"


def run(node, ctx):
    miss = missing_inputs(ctx, ["motor_2_path", "motor_lock", "motor_env", "dest_dir", "source_lock"])
    if miss:
        return result(node, Status.INCONCLUSIVE, gaps=[f"L05_INPUT_GAP:{k}" for k in miss])
    if not gate_open(node, ctx, GATE) or not Path(ctx["source_lock"]).is_file():
        return result(node, Status.BLOCKED, gaps=[f"APPROVAL_OR_SOURCE_LOCK_MISSING:{GATE}"])
    bad = verify_motor(Path(ctx["motor_2_path"]), Path(ctx["motor_lock"]), ctx.get("motor_2_id", "motor_2_queue_download_extract"))
    if bad:
        return result(node, Status.BLOCKED, gaps=bad)
    rc, rep, tail = run_motor(Path(ctx["motor_2_path"]), ctx["motor_env"], node.timeout_ms / 1000)
    verdict = str(rep.get("verdict", ""))
    ok = rc == 0 and bool(rep) and "GAP" not in verdict
    gaps = [] if ok else [f"MOTOR_RESULT_GAP:{verdict or 'rc=' + str(rc)}:{tail[-120:]}"]
    ev = [Evidence(kind="motor_report", ref=str(ctx["source_lock"]), sha256=sha256(rep))] if rep else []
    return result(node, Status.PASS if ok and ev else Status.FAIL, output=rep, evidence=ev, gaps=gaps,
                  touched=[ctx["dest_dir"]], actions=["download", "extract"])
