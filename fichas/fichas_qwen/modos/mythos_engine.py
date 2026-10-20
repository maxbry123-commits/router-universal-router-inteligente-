#!/usr/bin/env python3
"""mythos_engine.py - Motor deterministico del modo m09_mythos (Mythos mejorado x10).
El motor es el CONTROL (ledger, compuertas, convergencia, rollback). Las partes inteligentes (investigar, proponer,
ejecutar, verificar, auditar) son callbacks que conectas a tu modelo/herramientas.
Uso CLI: python3 mythos_engine.py mythos_engine.json   (valida la especificacion)"""
from __future__ import annotations
import copy, hashlib, json, re, sys, time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class MythosError(Exception):
    pass


def validate_spec(spec: dict) -> list:
    e = []
    ids = [i.get("id") for i in spec.get("improvements", [])]
    if ids != [f"M{n:02d}" for n in range(1, 11)]:
        e.append("improvements debe contener M01..M10 en orden")
    for i in spec.get("improvements", []):
        for k in ("name", "mechanism", "proof"):
            if not i.get(k):
                e.append(f"{i.get('id')}: falta '{k}'")
    c, caps = spec.get("config", {}), spec.get("caps", {})
    if not (1 <= c.get("max_cycles", 0) <= caps.get("max_cycles", 10)):
        e.append("config.max_cycles fuera de 1..caps.max_cycles")
    if not (0 <= c.get("max_research_depth", -1) <= caps.get("max_research_depth", 5)):
        e.append("config.max_research_depth fuera de tope")
    if c.get("min_findings_per_step", 0) < 1:
        e.append("min_findings_per_step debe ser >= 1 (compuerta de investigacion)")
    if c.get("min_hypotheses", 0) < 2:
        e.append("min_hypotheses debe ser >= 2")
    if c.get("stagnation_cycles_trigger", 0) < 1:
        e.append("stagnation_cycles_trigger debe ser >= 1")
    if not c.get("budget", {}).get("max_seconds", 0) > 0:
        e.append("budget.max_seconds requerido (>0)")
    if spec.get("escalation") != "none":
        e.append("escalation debe ser 'none'")
    if spec.get("terminal_states") != ["CONVERGED", "CONVERGED_WITH_BLOCKED", "TERMINATED_BY_LIMIT"]:
        e.append("terminal_states invalidos")
    return e


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def signature(gap_id: str, approach: str) -> str:
    return hashlib.sha256(f"{gap_id}|{norm(approach)}".encode("utf-8")).hexdigest()


def gaps_from_objective(obj: dict, default_severity: int = 3) -> list:
    """Gaps iniciales = cada criterio done_when del objetivo fijado (un gap por criterio, severidad uniforme)."""
    return [{"id": f"G{i + 1:02d}", "title": t, "severity": default_severity} for i, t in enumerate(obj["done_when"])]


@dataclass
class Gap:
    id: str
    title: str
    severity: int
    status: str = "open"
    evidence: list = field(default_factory=list)
    failed_signatures: list = field(default_factory=list)
    alternatives: list = field(default_factory=list)
    closed_cycle: Optional[int] = None
    block_reason: str = ""


class Ledger:
    def __init__(self):
        self.gaps: dict[str, Gap] = {}

    def add(self, g: dict):
        for k in ("id", "title", "severity"):
            if k not in g:
                raise MythosError(f"gap invalido: falta {k}")
        if not (1 <= int(g["severity"]) <= 5):
            raise MythosError("severidad fuera de 1..5")
        if g["id"] in self.gaps:
            raise MythosError(f"gap duplicado {g['id']}")
        self.gaps[g["id"]] = Gap(g["id"], g["title"], int(g["severity"]))

    def close(self, gid: str, evidence: list, cycle: int):
        ev = [x for x in (evidence or []) if isinstance(x, str) and x.strip()]
        if not ev:
            raise MythosError(f"cierre de {gid} sin evidencia (PASS sin evidencia prohibido)")
        g = self.gaps[gid]; g.status, g.evidence, g.closed_cycle = "closed", ev, cycle

    def reopen(self, gid: str, reason: str):
        g = self.gaps[gid]; g.status, g.closed_cycle = "open", None
        g.evidence = [f"reabierto por regresion: {reason}"]

    def block(self, gid: str, reason: str):
        g = self.gaps[gid]; g.status, g.block_reason = "blocked", reason

    def open_gaps(self):
        return sorted((g for g in self.gaps.values() if g.status == "open"), key=lambda g: (-g.severity, g.id))

    def open_count(self): return len(self.open_gaps())
    def score(self): return sum(g.severity for g in self.gaps.values() if g.status == "open")
    def by_status(self, s): return sorted(g.id for g in self.gaps.values() if g.status == s)


class MythosEngine:
    def __init__(self, spec: dict, *, research: Callable, propose: Callable, execute: Callable,
                 verify: Callable, audit: Callable, regress: Callable = lambda: [],
                 snapshot: Callable = lambda: None, restore: Callable = lambda tok: None,
                 now: Callable = time.monotonic, on_event: Optional[Callable] = None):
        errs = validate_spec(spec)
        if errs:
            raise MythosError("; ".join(errs))
        self.cfg = spec["config"]
        self.research, self.propose, self.execute, self.verify = research, propose, execute, verify
        self.audit, self.regress, self.snapshot, self.restore = audit, regress, snapshot, restore
        self.now, self.on_event = now, on_event
        self.events, self.research_log = [], []

    def _ev(self, name, **d):
        rec = {"event": name, **d}
        self.events.append(rec)
        if self.on_event:
            self.on_event(name, d)

    def run(self, initial_gaps: list) -> dict:
        cfg, L = self.cfg, Ledger()
        for g in initial_gaps:
            L.add(g)
        t0 = self.now()
        max_s = cfg["budget"]["max_seconds"]
        best = {"score": L.score(), "ledger": copy.deepcopy(L), "snap": self.snapshot()}
        stagnation, depth, c, state = 0, 0, 0, None
        self._ev("mythos_started", gaps=len(initial_gaps), score=L.score())

        while True:
            if self.now() - t0 >= max_s:
                state = "TERMINATED_BY_LIMIT"; self._ev("limit_reached", reason="time"); break
            if L.open_count() == 0:                                   # M10 auditoria final en frio
                a = self.audit()
                self._ev("final_audit", passed=bool(a.get("passed")))
                if a.get("passed") and a.get("evidence"):
                    state = "CONVERGED_WITH_BLOCKED" if L.by_status("blocked") else "CONVERGED"
                    break
                new = a.get("new_gaps", [])
                for g in new:
                    if g["id"] not in L.gaps:
                        L.add(g)
                if L.open_count() == 0:                                # fallo sin gaps: fail-closed
                    L.add({"id": f"audit_fail_{c}", "title": "Auditoria final fallo sin evidencia ni gaps nuevos", "severity": 5})
                best["score"] = max(best["score"], L.score())          # la auditoria puede subir el score legitimamente
                best["ledger"], best["snap"] = copy.deepcopy(L), self.snapshot()
            if c >= cfg["max_cycles"]:
                state = "TERMINATED_BY_LIMIT"; self._ev("limit_reached", reason="max_cycles"); break
            c += 1
            self._ev("cycle_started", cycle=c, open=L.open_count(), depth=depth)
            slice_s = (max_s - (self.now() - t0)) / (cfg["max_cycles"] - c + 1)   # M07 rollover implicito
            cycle_t0 = self.now()

            for gap in L.open_gaps():
                if self.now() - cycle_t0 >= slice_s:
                    self._ev("cycle_slice_exhausted", cycle=c); break
                # M02 compuerta de investigacion
                raw = self.research(gap, depth) or []
                seen, findings = set(), []
                for f in raw:
                    src = (f.get("source") or "").strip()
                    if src and src not in seen:
                        seen.add(src); findings.append(f)
                if len(findings) < cfg["min_findings_per_step"]:
                    self._ev("research_gate_blocked", gap=gap.id, cycle=c); continue
                self.research_log.append({"cycle": c, "gap": gap.id, "sources": [f["source"] for f in findings]})
                # M03 multi-hipotesis + M08 memoria negativa
                proposals = [a for a in (self.propose(gap, findings, list(gap.failed_signatures), depth) or []) if a and a.strip()]
                uniq = list(dict.fromkeys(norm(a) for a in proposals))
                if len(uniq) < cfg["min_hypotheses"]:
                    self._ev("hypotheses_gate_blocked", gap=gap.id, got=len(uniq)); continue
                fresh = [a for a in proposals if signature(gap.id, a) not in gap.failed_signatures]
                if not fresh:
                    self._ev("approaches_exhausted", gap=gap.id, cycle=c); continue
                chosen = fresh[0]
                gap.alternatives = [a for a in fresh[1:]]
                sig = signature(gap.id, chosen)
                res = self.execute(gap, chosen)
                ver = self.verify(gap, res)                              # M04 verificador independiente
                if ver.get("passed") and any(isinstance(x, str) and x.strip() for x in ver.get("evidence", [])):
                    L.close(gap.id, ver["evidence"], c)
                    self._ev("gap_closed", gap=gap.id, cycle=c)
                else:
                    gap.failed_signatures.append(sig)
                    self._ev("approach_failed", gap=gap.id, cycle=c)

            for gid in (self.regress() or []):                            # M06 guarda de regresion
                if gid in L.gaps and L.gaps[gid].status == "closed":
                    L.reopen(gid, "regress() detecto fallo"); self._ev("regression_reopened", gap=gid, cycle=c)

            score = L.score()                                             # M05 convergencia
            if score < best["score"]:
                best = {"score": score, "ledger": copy.deepcopy(L), "snap": self.snapshot()}
                stagnation = 0
            else:
                stagnation += 1
                if cfg["best_so_far_rollback"] and score > best["score"]:  # M09 rollback al mejor estado
                    self.restore(best["snap"])
                    cur, L = L, copy.deepcopy(best["ledger"])
                    for gid, g in L.gaps.items():                           # M08: la memoria negativa sobrevive al rollback
                        for sg in cur.gaps.get(gid, Gap(gid, "", 1)).failed_signatures:
                            if sg not in g.failed_signatures:
                                g.failed_signatures.append(sg)
                    self._ev("rolled_back_to_best", cycle=c, best_score=best["score"])
                if stagnation >= cfg["stagnation_cycles_trigger"]:
                    if depth < cfg["max_research_depth"]:
                        depth += 1; self._ev("depth_raised", depth=depth, cycle=c)
                    else:
                        for g in L.open_gaps():
                            L.block(g.id, f"sin progreso tras profundidad {depth}; ultima evidencia: {g.failed_signatures[-1:] or 'sin intentos'}")
                            self._ev("gap_blocked_with_evidence", gap=g.id, cycle=c)
                    stagnation = 0
            self._ev("cycle_closed", cycle=c, score=L.score(), open=L.open_count())

        return {"state": state, "cycles": c, "closed": L.by_status("closed"), "blocked": L.by_status("blocked"),
                "open": L.by_status("open"), "best_score": best["score"], "final_score": L.score(),
                "research_log": self.research_log,
                "ledger": {gid: {"status": g.status, "severity": g.severity, "evidence": g.evidence,
                                 "failed_approaches": len(g.failed_signatures), "alternatives": g.alternatives,
                                 "block_reason": g.block_reason} for gid, g in L.gaps.items()},
                "events": self.events}


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "mythos_engine.json", encoding="utf-8"))
    errs = validate_spec(spec)
    if errs:
        print("VEREDICTO: FAIL"); [print(" -", x) for x in errs]; sys.exit(1)
    print("VEREDICTO: PASS (especificacion Mythos x10 valida: M01..M10, tope de ciclos y compuertas)")
