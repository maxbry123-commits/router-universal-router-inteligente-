#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, pathlib, shutil, subprocess, time, urllib.parse

SCHEMA = "yaiwes.frontend.move-batches.v1"
MODE = os.getenv("MODE", "disk").lower()
SOURCE_DIR = pathlib.Path(os.getenv("SOURCE_DIR", "")).expanduser()
DEST_DIR = pathlib.Path(os.getenv("DEST_DIR", "")).expanduser()
STATE_FILE = pathlib.Path(os.getenv("STATE_FILE", ".motor4-move-state.json")).expanduser()
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "25"))
COLLISION_POLICY = os.getenv("COLLISION_POLICY", "fail").lower()
MAX_BATCHES = int(os.getenv("MAX_BATCHES", "0"))

# ================= MODE=git =================
# Mueve rutas DENTRO de un repo de GitHub con UN commit por lote (API git trees).
# No clona, no descarga contenido, no usa disco, no LFS, no GitHub Actions, nunca force.
# Mover = la ruta destino apunta al MISMO objeto git (arbol o blob) y la ruta origen se borra.
# Autenticacion: la resuelve el entorno via `gh` (R4: este codigo no lee ni imprime tokens).
# Entradas: REPO=owner/repo  BRANCH  MOVES_FILE=json [{"src":"a/x","dst":"b/x"}]  BATCH_SIZE  COLLISION_POLICY
REPO = os.getenv("REPO", "")
BRANCH = os.getenv("BRANCH", "")
MOVES_FILE = os.getenv("MOVES_FILE", "")


def gh(method, path, body=None):
    cmd = ["gh", "api", "-X", method, "-H", "Accept: application/vnd.github+json", "-i", path]
    if body is not None:
        cmd += ["--input", "-"]
    p = subprocess.run(cmd, input=None if body is None else json.dumps(body), capture_output=True, text=True)
    head, _, data = p.stdout.partition("\r\n\r\n") if "\r\n\r\n" in p.stdout else p.stdout.partition("\n\n")
    try:
        status = int(head.split()[1])
    except Exception:
        raise RuntimeError("GH_CLI_GAP:" + (p.stderr.strip()[:200] or "sin salida"))
    return status, (json.loads(data) if data.strip() else None)


def q(p):
    return urllib.parse.quote(p.strip("/"), safe="/")


def entry_of(commit_sha, path):
    parent, _, name = path.strip("/").rpartition("/")
    st, data = gh("GET", f"/repos/{REPO}/contents/{q(parent)}?ref={commit_sha}")
    if st == 404:
        return None
    if st != 200 or not isinstance(data, list):
        raise RuntimeError(f"LIST_GAP:{st}:{parent}")
    if len(data) >= 1000:
        raise RuntimeError("LIST_LIMIT_GAP:" + parent)
    for e in data:
        if e["name"] == name:
            if e["type"] == "dir":
                return {"type": "tree", "mode": "040000", "sha": e["sha"]}
            if e["type"] == "file":
                return {"type": "blob", "mode": "100644", "sha": e["sha"]}
            raise RuntimeError("SOURCE_SYMLINK_GAP:" + path)
    return None


def git_mode():
    if not REPO or not BRANCH or not MOVES_FILE:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "REPO, BRANCH y MOVES_FILE obligatorios"}))
    moves = json.loads(pathlib.Path(MOVES_FILE).read_text())
    if not moves:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "MOVES_FILE vacio"}))
    for m in moves:
        s, d = m["src"].strip("/"), m["dst"].strip("/")
        if s == d or d.startswith(s + "/"):
            raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "DEST_INSIDE_SOURCE_GAP", "detail": s}))
        if s.startswith(d + "/"):
            raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "SOURCE_INSIDE_DEST_GAP", "detail": s}))
    results, failed = {}, {}
    for start in range(0, len(moves), BATCH_SIZE):
        batch = moves[start:start + BATCH_SIZE]
        try:
            for attempt in range(1, 9):
                st, ref = gh("GET", f"/repos/{REPO}/git/ref/heads/{q(BRANCH)}")
                if st != 200:
                    raise RuntimeError(f"SOURCE_REF_GAP:{st}")
                head = ref["object"]["sha"]
                _, commit = gh("GET", f"/repos/{REPO}/git/commits/{head}")
                items, plan = [], []
                for m in batch:
                    s, d = m["src"].strip("/"), m["dst"].strip("/")
                    src, dst = entry_of(head, s), entry_of(head, d)
                    if src is None:
                        if dst is not None:
                            results[s] = "VERIFIED_EXISTING_AFTER_MOVE"; continue
                        raise RuntimeError("SOURCE_MISSING_AND_DEST_UNVERIFIED:" + s)
                    if dst is not None and dst["sha"] != src["sha"]:
                        if COLLISION_POLICY == "skip":
                            results[s] = "SKIPPED_COLLISION"; continue
                        if COLLISION_POLICY != "replace":
                            raise RuntimeError("DESTINATION_COLLISION:" + d)
                    if dst is None or dst["sha"] != src["sha"]:
                        items.append({"path": d, "mode": src["mode"], "type": src["type"], "sha": src["sha"]})
                    items.append({"path": s, "mode": src["mode"], "type": src["type"], "sha": None})
                    plan.append((s, d, src["sha"]))
                if not items:
                    break
                st, tree = gh("POST", f"/repos/{REPO}/git/trees", {"base_tree": commit["tree"]["sha"], "tree": items})
                if st != 201:
                    raise RuntimeError(f"TREE_GAP:{st}")
                st, new = gh("POST", f"/repos/{REPO}/git/commits", {"message": f"move(motor_4): {len(plan)} rutas", "tree": tree["sha"], "parents": [head]})
                if st != 201:
                    raise RuntimeError(f"COMMIT_GAP:{st}")
                st, _ = gh("PATCH", f"/repos/{REPO}/git/refs/heads/{q(BRANCH)}", {"sha": new["sha"], "force": False})
                if st == 200:
                    for s, d, sha in plan:
                        got = entry_of(new["sha"], d)
                        if got is None or got["sha"] != sha:
                            raise RuntimeError("READBACK_HASH_MISMATCH:" + d)
                        if entry_of(new["sha"], s) is not None:
                            raise RuntimeError("SOURCE_STILL_PRESENT:" + s)
                        results[s] = "MOVED_VERIFIED"
                    break
                if st in (409, 422) and attempt < 8:
                    time.sleep(2 * attempt); continue
                raise RuntimeError(f"NON_FAST_FORWARD_CONFLICT:{st}")
            time.sleep(1)
        except RuntimeError as e:
            for m in batch:
                if m["src"].strip("/") not in results:
                    failed[m["src"].strip("/")] = str(e)
            if COLLISION_POLICY == "fail":
                break
    total, done = len(moves), len(results)
    print(json.dumps({"schema": SCHEMA, "mode": "git", "repo": REPO, "branch": BRANCH, "total": total,
                      "moved_or_verified": done, "failed": len(failed), "pending": total - done,
                      "results": results, "errors": failed,
                      "verdict": "VERIFIED_CLOSED" if done == total and not failed else "GAPS_PENDING"},
                     ensure_ascii=False, sort_keys=True))

# ================= MODE=disk (original, sin cambios) =================

def guard_roots():
    if not str(SOURCE_DIR) or not str(DEST_DIR):
        raise RuntimeError("SOURCE_DIR and DEST_DIR required")
    s = SOURCE_DIR.resolve(); d = DEST_DIR.resolve()
    if s == d or s in d.parents:
        raise RuntimeError("DEST_INSIDE_SOURCE_GAP")
    if d in s.parents:
        raise RuntimeError("SOURCE_INSIDE_DEST_GAP")


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def first_manifest():
    if not SOURCE_DIR.is_dir():
        raise RuntimeError("SOURCE_DIR_NOT_FOUND")
    rows = []
    for p in sorted((x for x in SOURCE_DIR.rglob("*") if x.is_file()), key=lambda x: x.relative_to(SOURCE_DIR).as_posix()):
        if p.is_symlink():
            raise RuntimeError("SOURCE_SYMLINK_GAP:" + p.relative_to(SOURCE_DIR).as_posix())
        if p.resolve() == STATE_FILE.resolve():
            continue
        rows.append({"rel": p.relative_to(SOURCE_DIR).as_posix(), "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    return rows


def load_state():
    files = first_manifest()
    fresh = {"schema": SCHEMA, "manifest": files, "completed": {}, "failed": {}, "batches": 0}
    if not STATE_FILE.exists():
        return fresh
    old = json.loads(STATE_FILE.read_text())
    by_rel = {r["rel"]: r for r in files}
    completed = {}
    for rel, status in old.get("completed", {}).items():
        row = by_rel.get(rel); dst = DEST_DIR / rel
        if row and dst.is_file() and sha256_file(dst) == row["sha256"]:
            completed[rel] = status
    fresh["completed"] = completed
    fresh["batches"] = old.get("batches", 0)
    return fresh


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_name(STATE_FILE.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, STATE_FILE)


def move_verified(row):
    rel = pathlib.PurePosixPath(row["rel"]); src = SOURCE_DIR / rel; dst = DEST_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        if dst.exists() and sha256_file(dst) == row["sha256"]:
            return "VERIFIED_EXISTING_AFTER_MOVE"
        raise RuntimeError("SOURCE_MISSING_AND_DEST_UNVERIFIED:" + row["rel"])
    if sha256_file(src) != row["sha256"]:
        raise RuntimeError("SOURCE_CHANGED:" + row["rel"])
    if dst.exists():
        dsha = sha256_file(dst)
        if dsha == row["sha256"]:
            src.unlink(); return "DEST_IDENTICAL_SOURCE_REMOVED"
        if COLLISION_POLICY == "skip":
            return "SKIPPED_COLLISION"
        if COLLISION_POLICY != "replace":
            raise RuntimeError("DESTINATION_COLLISION:" + row["rel"])
    tmp = dst.with_name(dst.name + ".moving")
    if tmp.exists(): tmp.unlink()
    shutil.move(str(src), str(tmp))
    if sha256_file(tmp) != row["sha256"]:
        if not src.exists(): shutil.move(str(tmp), str(src))
        raise RuntimeError("MOVE_HASH_MISMATCH:" + row["rel"])
    os.replace(tmp, dst)
    if sha256_file(dst) != row["sha256"]:
        raise RuntimeError("READBACK_HASH_MISMATCH:" + row["rel"])
    return "MOVED_VERIFIED"


def cleanup_empty_dirs():
    if not SOURCE_DIR.exists(): return
    for d in sorted((x for x in SOURCE_DIR.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
        try: d.rmdir()
        except OSError: pass


def main():
    if not 1 <= BATCH_SIZE <= 100:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "BATCH_SIZE must be 1..100"}))
    if COLLISION_POLICY not in {"fail", "skip", "replace"}:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "COLLISION_POLICY must be fail|skip|replace"}))
    if MODE == "git":
        return git_mode()
    if MODE != "disk":
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": "MODE must be git|disk"}))
    try:
        guard_roots()
    except RuntimeError as e:
        raise SystemExit(json.dumps({"schema": SCHEMA, "verdict": "INPUT_GAP", "detail": str(e)}))
    state = load_state(); completed = state.setdefault("completed", {}); batches = 0
    while True:
        pending = [r for r in state["manifest"] if r["rel"] not in completed]
        if not pending or (MAX_BATCHES and batches >= MAX_BATCHES): break
        for row in pending[:BATCH_SIZE]:
            try:
                status = move_verified(row); completed[row["rel"]] = status; state.setdefault("failed", {}).pop(row["rel"], None)
            except Exception as e:
                state.setdefault("failed", {})[row["rel"]] = str(e)
        batches += 1; state["batches"] = state.get("batches", 0) + 1; save_state(state)
        if state.get("failed") and COLLISION_POLICY == "fail": break
    cleanup_empty_dirs()
    total = len(state["manifest"]); done = len(completed); failed = len(state.get("failed", {})); pending_count = total - done
    source_remaining = sum(1 for p in SOURCE_DIR.rglob("*") if p.is_file()) if SOURCE_DIR.exists() else 0
    result = {
        "schema": SCHEMA, "batch_size": BATCH_SIZE, "collision_policy": COLLISION_POLICY,
        "total": total, "moved_or_verified": done, "failed": failed, "pending": pending_count,
        "source_files_remaining": source_remaining, "batches_total": state.get("batches", 0),
        "state_file": str(STATE_FILE), "verdict": "VERIFIED_CLOSED" if pending_count == 0 and failed == 0 else "GAPS_PENDING"
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__": main()
