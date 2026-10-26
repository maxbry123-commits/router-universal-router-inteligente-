#!/usr/bin/env python3
"""loop_controller.py - Controlador del bucle NO-STOP sobre el contrato DAG v1.1 (la pieza 'iniciar_bucle').
Bucle EXTERNO y deterministico: elige nodos listos, llama a tu executor (LLM + herramientas), verifica con checks
deterministas, aplica la escalera on_stuck y respeta topes duros. PASS solo por evidencia de checks (nunca por autoinforme).
El executor es un callable que TU conectas:  executor(node: dict, ctx: dict) -> dict
   devuelve (opcional) {"output": str, "actions": list, "cost_usd": float}
   ctx trae: attempt, errors (de intentos previos), flags (force_different, switch_model_tier, reset_context, ...), workdir.
Este controlador ejecuta nodos de a uno (referencia). El paralelismo del modo orquestador usa ParallelPool de mode_router.py.
Los comandos de los checks se ejecutan SIN shell (shlex.split): no uses pipes ni redirecciones en 'command'."""
from __future__ import annotations
import collections, fnmatch, hashlib, json, os, re, shlex, subprocess, time
from typing import Callable, Optional

import validate_contract as base
import objective_store

TERMINAL = {"passed", "blocked_with_evidence", "skipped"}


class LoopError(Exception):
    pass


# ---------------------------------------------------------------- checks deterministas
def _tail(s: str, n: int = 300) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s[-n:]


def run_check(chk: dict, workdir: str) -> dict:
    kind, spec, cid = chk["kind"], chk.get("spec", {}), chk["id"]
    def res(ok, ev): return {"id": cid, "kind": kind, "required": chk.get("required", True), "passed": bool(ok), "evidence": ev}
    try:
        if kind == "file_exists":
            miss = [p for p in spec.get("paths", []) if not os.path.exists(os.path.join(workdir, p))]
            return res(not miss and bool(spec.get("paths")), "todos presentes" if not miss else f"faltan: {miss}")
        if kind in ("command", "test_suite"):
            args = shlex.split(spec["command"])
            exp = (chk.get("expect") or {}).get("exit_code", 0)
            p = subprocess.run(args, cwd=workdir, capture_output=True, text=True, timeout=chk.get("timeout_s", 600))
            return res(p.returncode == exp, f"exit={p.returncode} esperado={exp} salida=...{_tail(p.stdout + p.stderr)}")
        if kind == "regex_match":
            txt = open(os.path.join(workdir, spec["file"]), encoding="utf-8", errors="ignore").read()
            ok = re.search(spec["pattern"], txt, re.S) is not None
            return res(ok, f"patron {'encontrado' if ok else 'NO encontrado'} en {spec['file']}")
        if kind == "json_schema":
            try:
                import jsonschema
            except ImportError:
                return res(False, "jsonschema no instalado: no se puede verificar (fail-closed)")
            inst = json.load(open(os.path.join(workdir, spec["file"]), encoding="utf-8"))
            sch = json.load(open(os.path.join(workdir, spec["schema"]), encoding="utf-8"))
            errs = list(jsonschema.Draft202012Validator(sch).iter_errors(inst))
            return res(not errs, "esquema valido" if not errs else f"{len(errs)} errores: {errs[0].message}")
        if kind == "git_state":
            bad = []
            for dp, dn, fn in os.walk(workdir):
                dn[:] = [d for d in dn if d not in {".git", "node_modules", "__pycache__"}]
                for f in fn:
                    try:
                        for ln in open(os.path.join(dp, f), encoding="utf-8"):
                            if re.match(r"^(<{7} |>{7} )", ln):
                                bad.append(os.path.relpath(os.path.join(dp, f), workdir)); break
                    except (UnicodeDecodeError, OSError):
                        continue
            return res(not bad, "sin marcadores de conflicto" if not bad else f"conflictos en {bad[:5]}")
        if kind == "diff_scope":
            g = subprocess.run(["git", "-C", workdir, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
            if g.returncode != 0:
                return res(False, "no es repo git: no se puede verificar el alcance (fail-closed)")
            st = subprocess.run(["git", "-C", workdir, "status", "--porcelain"], capture_output=True, text=True).stdout
            changed = [ln[3:].split(" -> ")[-1].strip().strip('"') for ln in st.splitlines() if ln.strip()]
            out = [c for c in changed if not any(fnmatch.fnmatch(c, pat) for pat in spec["allowed_globs"])]
            return res(not out, f"{len(changed)} cambios dentro del alcance" if not out else f"fuera de alcance: {out[:5]}")
        return res(False, f"kind '{kind}' no soportado por este controlador (fail-closed)")
    except subprocess.TimeoutExpired:
        return res(False, "timeout del check")
    except Exception as ex:  # noqa: BLE001
        return res(False, f"error al ejecutar el check: {ex!r}")


# ---------------------------------------------------------------- controlador
class LoopController:
    def __init__(self, contract: dict, executor: Callable, workdir: str, *, limits: Optional[dict] = None,
                 now: Callable = time.monotonic, on_event: Optional[Callable] = None,
                 ladder_handlers: Optional[dict] = None, objective_path: Optional[str] = None):
        errs = base.dag_errors(contract) + base.router_errors(contract) + base.loop_errors(contract)
        if errs:
            raise LoopError("contrato invalido: " + "; ".join(errs))
        self.c, self.exec, self.workdir, self.now, self.on_event = contract, executor, workdir, now, on_event
        L = contract["loop"]
        self.limits = {**L["hard_limits"], **(limits or {})}
        self.ladder = L["on_stuck"]["ladder"]
        self.handlers = ladder_handlers or {}
        self.token = L["completion"]["promise_token"]
        self.nodes = {n["id"]: n for n in contract["dag"]["nodes"]}
        self.deps = {nid: [] for nid in self.nodes}
        for e in contract["dag"]["edges"]:
            self.deps[e["to"]].append((e["from"], e.get("condition", "on_passed")))
        g = contract.get("anti_repeat_guard", {}).get("dedupe_tool_calls", {"window": 12, "max_identical": 2})
        self.window = collections.deque(maxlen=g["window"]); self.max_identical = g["max_identical"]
        self.st = {nid: {"status": "pending", "attempts": 0, "ladder_idx": 0, "errors": [], "evidence": [], "flags": {}}
                   for nid in self.nodes}
        self.progress_path = os.path.join(workdir, L["state"]["progress_file"])
        self.events_path = os.path.join(workdir, contract.get("observability", {}).get("event_log", "state/events.jsonl"))
        self.objective_path = objective_path
        self.obj_hash = objective_store.objective_hash(objective_store.read_objective(objective_path)) if objective_path and objective_store.read_objective(objective_path) else None
        self.iteration, self.cost, self.no_progress, self.t0 = 0, 0.0, 0, None
        os.makedirs(os.path.dirname(self.progress_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.events_path), exist_ok=True)

    # ---- util
    def _ev(self, name, **d):
        rec = {"t": round(self.now() - (self.t0 or self.now()), 3), "event": name, **d}
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if self.on_event:
            self.on_event(name, d)

    def _save(self):
        tasks = [{"id": nid, "status": s["status"], "attempts": s["attempts"], "evidence": s["evidence"],
                  "errors": s["errors"][-3:]} for nid, s in self.st.items()]
        doc = {"contract_id": self.c["contract_id"], "iteration": self.iteration, "cost_usd": round(self.cost, 4), "tasks": tasks}
        tmp = self.progress_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.progress_path)

    def _dep_state(self, nid):
        wait = False
        for d, cond in self.deps[nid]:
            s = self.st[d]["status"]
            if cond == "on_passed":
                if s == "passed": continue
                if s in TERMINAL: return "dead"
                wait = True
            else:
                if s in TERMINAL: continue
                wait = True
        return "wait" if wait else "ready"

    def _block(self, nid, reason):
        s = self.st[nid]; s["status"] = "blocked_with_evidence"
        s["evidence"] = [reason] + [str(e) for e in s["errors"][-2:]]
        self._ev("task_blocked", node=nid, reason=reason); self._save()

    def _limit(self):
        lim = self.limits
        if self.iteration >= lim["max_iterations"]: return "max_iterations"
        if self.now() - self.t0 >= lim["max_wall_clock_s"]: return "max_wall_clock_s"
        if self.cost >= lim["max_cost_usd"]: return "max_cost_usd"
        if self.no_progress >= lim["max_consecutive_no_progress"]: return "max_consecutive_no_progress"
        return None

    def _exhausted(self, nid):
        node, s = self.nodes[nid], self.st[nid]
        if node["retry"]["on_exhausted"] == "mark_blocked_with_evidence_and_continue":
            return self._block(nid, "reintentos agotados")
        idx = s["ladder_idx"]; s["ladder_idx"] += 1
        step = self.ladder[min(idx, len(self.ladder) - 1)]
        self._ev("stuck_ladder_step", node=nid, step=step)
        if step == "mark_blocked_with_evidence_and_continue" or idx >= len(self.ladder) - 1:
            return self._block(nid, "escalera on_stuck agotada")
        s["flags"][step] = True
        if step in self.handlers:
            self.handlers[step](node, s, self)
        s["attempts"] = 0

    # ---- bucle
    def run(self) -> dict:
        self.t0 = self.now()
        self._ev("loop_started", contract=self.c["contract_id"]); self._save()
        reason = None
        while True:
            changed = True
            while changed:                                    # propagar bloqueos a dependientes
                changed = False
                for nid in self.nodes:
                    if self.st[nid]["status"] == "pending" and self._dep_state(nid) == "dead":
                        self._block(nid, "dependencia bloqueada"); changed = True
            if all(s["status"] in TERMINAL for s in self.st.values()):
                break
            reason = self._limit()
            if reason:
                self._ev("limit_reached", reason=reason); break
            if self.obj_hash:
                try:
                    objective_store.assert_unchanged(self.objective_path, self.obj_hash)
                except objective_store.ObjectiveError:
                    reason = "objective_drift"; self._ev("limit_reached", reason=reason); break
            ready = sorted(n for n, s in self.st.items() if s["status"] == "pending" and self._dep_state(n) == "ready")
            if not ready:
                reason = "deadlock"; self._ev("limit_reached", reason=reason); break
            nid = ready[0]; node, s = self.nodes[nid], self.st[nid]
            self.iteration += 1; s["attempts"] += 1; s["status"] = "running"
            self._ev("node_started", node=nid, attempt=s["attempts"])
            ctx = {"attempt": s["attempts"], "errors": list(s["errors"][-3:]), "flags": dict(s["flags"]), "workdir": self.workdir}
            try:
                out = self.exec(node, ctx) or {}
            except Exception as ex:  # noqa: BLE001
                out = {"output": f"executor lanzo {ex!r}"}; s["errors"].append(f"executor: {ex!r}")
            self.cost += float(out.get("cost_usd", 0) or 0)
            sig = hashlib.sha256(json.dumps(out.get("actions", out.get("output", "")), sort_keys=True, default=str).encode()).hexdigest()
            self.window.append(sig)
            if self.window.count(sig) > self.max_identical:
                s["flags"]["force_different"] = True; self._ev("repeat_detected", node=nid)
            s["status"] = "verifying"
            results = [run_check(c, self.workdir) for c in node["acceptance"]]
            req_ok = all(r["passed"] for r in results if r["required"]) and any(r["required"] for r in results)
            if req_ok:
                s["status"] = "passed"; s["evidence"] = [f"{r['id']}: {r['evidence']}" for r in results]
                s["flags"].pop("force_different", None); s["errors"] = []; self.no_progress = 0
                self._ev("node_passed", node=nid, attempts=s["attempts"])
            else:
                s["status"] = "pending"; self.no_progress += 1
                s["errors"].append("; ".join(f"{r['id']}: {r['evidence']}" for r in results if not r["passed"]))
                self._ev("node_failed", node=nid, attempt=s["attempts"])
                if s["attempts"] >= node["retry"]["max_attempts"]:
                    self._exhausted(nid)
            self._save()
        return self._report(reason)

    def _report(self, limit_reason):
        terminal_ok = all(s["status"] in TERMINAL for s in self.st.values())
        blocked = [n for n, s in self.st.items() if s["status"] == "blocked_with_evidence"]
        if limit_reason or not terminal_ok:
            state = "TERMINATED_BY_LIMIT"
        else:
            state = "DONE_WITH_BLOCKED" if blocked else "DONE"
        self._ev("terminal", state=state); self._save()
        return {"state": state, "limit_reason": limit_reason, "iterations": self.iteration,
                "elapsed_s": round(self.now() - self.t0, 3), "cost_usd": round(self.cost, 4), "blocked": blocked,
                "promise_token": self.token if state in ("DONE", "DONE_WITH_BLOCKED") else None,
                "nodes": {n: {"status": s["status"], "attempts": s["attempts"], "evidence": s["evidence"]} for n, s in self.st.items()}}
