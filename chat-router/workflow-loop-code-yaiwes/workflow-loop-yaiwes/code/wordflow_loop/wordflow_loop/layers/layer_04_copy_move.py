from __future__ import annotations
from pathlib import Path
from ..contracts import Evidence, Status, sha256
from ._common import gate_open, missing_inputs, result, run_motor, verify_motor

LAYER = "L04_COPY_MOVE"
GATE = "DIRECTOR_APPROVAL_REQUIRED"


def run(node, ctx):
    op = ctx.get("op", "copy")
    motor_key, motor_id = ("motor_3_path", "motor_3_copy_batches") if op == "copy" else ("motor_4_path", "motor_4_move_batches")
    miss = missing_inputs(ctx, [motor_key, "motor_lock", "source_dir", "dest_dir", "state_file", "batch_size"])
    if miss:
        return result(node, Status.INCONCLUSIVE, gaps=[f"L04_INPUT_GAP:{k}" for k in miss])
    if not gate_open(node, ctx, GATE):
        return result(node, Status.BLOCKED, gaps=[f"APPROVAL_MISSING:{GATE}"])
    bad = verify_motor(Path(ctx[motor_key]), Path(ctx["motor_lock"]), motor_id)
    if bad:
        return result(node, Status.BLOCKED, gaps=bad)
    env = {"SOURCE_DIR": ctx["source_dir"], "DEST_DIR": ctx["dest_dir"], "STATE_FILE": ctx["state_file"],
           "BATCH_SIZE": ctx["batch_size"], "COLLISION_POLICY": ctx.get("collision_policy", "fail")}
    rc, rep, tail = run_motor(Path(ctx[motor_key]), env, node.timeout_ms / 1000)
    ok = rc == 0 and rep.get("failed", 1) == 0 and rep.get("pending", 1) == 0
    gaps = [] if ok else [f"MOTOR_RESULT_GAP:{rep.get('verdict', 'rc=' + str(rc))}:{tail[-120:]}"]
    ev = [Evidence(kind="motor_report", ref=str(ctx["state_file"]), sha256=sha256(rep))] if rep else []
    return result(node, Status.PASS if ok and ev else Status.FAIL, output=rep, evidence=ev, gaps=gaps,
                  touched=[ctx["dest_dir"]], actions=[op])
