"""exec_dispatch.py - Reintento con fallback POR NODO: prueba combinaciones (modelo, layout) hasta que una EJECUTE.
Detecta acuse de recibo y HERRAMIENTA_NO_EJECUTADA, aprende que combinacion funciona por modelo y deja evidencia.
Se conecta como 'executor' del LoopController. Requiere prompt_layouts.py."""
import json, os, re, tempfile
import prompt_layouts as pl

EXTRA_ACK_PATTERNS = [
    r"(?i)\bestoy\s+(listo|lista|preparad[oa]|a\s+la\s+espera|esperando|atent[oa])\b",
    r"(?i)\ba\s+la\s+espera\s+de\b", r"(?i)\bquedo\s+(a\s+la\s+espera|atent[oa])\b",
    r"(?i)\bcuando\s+(quieras|est[eé]s\s+list[oa]|me\s+indiques)\b", r"(?i)^\s*listo[.,:;!]?\s*$",
    r"(?i)^\s*listo[.,:;!]", r"(?i)\b(dime|ind[ií]came|cu[eé]ntame)\s+(qu[eé]|cu[aá]l|en\s+qu[eé])\b",
    r"(?i)en\s+qu[eé]\s+(puedo|te\s+puedo)\s+ayudar", r"(?i)\bi'?m\s+ready\b", r"(?i)\bready\s+(when|for)\b",
    r"(?i)\bwaiting\s+for\s+(your|the)\b",
]
WORKSPACE_CHECKS = {"file_exists", "command", "test_suite", "regex_match", "git_state", "diff_scope", "json_schema"}


def expects_tools_for(node: dict) -> bool:
    """Si el nodo se acepta mirando el workspace, el modelo DEBE llamar herramientas (texto solo no sirve)."""
    return any(c.get("kind") in WORKSPACE_CHECKS for c in node.get("acceptance", []))


def classify(resp: dict, expects_tools: bool, min_chars: int = 400) -> str:
    text, calls = (resp.get("text") or "").strip(), resp.get("tool_calls") or []
    if calls:
        return "OK"
    if not text:
        return "VACIO"
    if len(text) < min_chars and (pl.is_ack_only(text, None, min_chars)[0]
                                  or any(re.search(p, text) for p in EXTRA_ACK_PATTERNS)):
        return "ACK"
    return "HERRAMIENTA_NO_EJECUTADA" if expects_tools else "OK"


class Profile:
    """Memoria por (modelo|layout): ok/fail/consec_fail. Persistente y atomica."""
    def __init__(self, path=None):
        self.path, self.d = path, {}
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.d = json.load(f)

    @staticmethod
    def _k(m, l): return f"{m}|{l}"
    def _e(self, m, l): return self.d.get(self._k(m, l), {"ok": 0, "fail": 0, "consec_fail": 0})
    def score(self, m, l): e = self._e(m, l); return (e["ok"] + 1) / (e["ok"] + e["fail"] + 2)
    def consec(self, m, l): return self._e(m, l)["consec_fail"]

    def record(self, m, l, ok: bool):
        e = self._e(m, l)
        if ok: e["ok"] += 1; e["consec_fail"] = 0
        else: e["fail"] += 1; e["consec_fail"] += 1
        self.d[self._k(m, l)] = e
        if self.path:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(self.path)))
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.d, f, indent=2)
            os.replace(tmp, self.path)

    def ordered(self, models, layouts, quarantine_after):
        combos = [(m, l) for l in layouts for m in models]            # empate: layout primero, luego orden de modelos
        idx = {c: i for i, c in enumerate(combos)}
        key = lambda c: (-self.score(*c), idx[c])
        healthy = [c for c in combos if self.consec(*c) < quarantine_after]
        return sorted(healthy, key=key) + sorted([c for c in combos if c not in healthy], key=key)  # en cuarentena: al final


def default_task(node: dict, ctx: dict) -> str:
    t = node.get("instruction") or node["title"]
    errs = ctx.get("errors") or []
    return t + ("\n\nErrores del intento anterior (corrigelos):\n" + "\n".join(f"- {e}" for e in errs) if errs else "")


class ExecDispatcher:
    def __init__(self, call_model, run_tools, models, profile_path=None, layouts=None, max_attempts=8,
                 min_chars=400, quarantine_after=6, on_event=None):
        self.call_model, self.run_tools, self.models = call_model, run_tools, list(models)
        self.layouts = list(layouts or pl.DEFAULT_ORDER)
        self.profile, self.max_attempts, self.min_chars = Profile(profile_path), max_attempts, min_chars
        self.quarantine_after, self.on_event, self.last = quarantine_after, on_event, {}

    def execute(self, node, gobernanza, tarea, expects_tools=None, exclude=()):
        expects = expects_tools_for(node) if expects_tools is None else expects_tools
        excl, tried, cost = set(exclude), [], 0.0
        for m, l in self.profile.ordered(self.models, self.layouts, self.quarantine_after):
            if (m, l) in excl:
                continue
            if len(tried) >= self.max_attempts:
                break
            msgs = pl.assemble(l, gobernanza, tarea)
            sha = pl.assert_task_present(msgs, tarea)
            results = None
            try:
                resp = self.call_model(m, msgs) or {}
                code = classify(resp, expects, self.min_chars)
            except Exception as ex:  # noqa: BLE001  (red/API: no envenena el perfil)
                resp, code = {}, "MODEL_ERROR"
            if code == "OK" and resp.get("tool_calls"):
                try:
                    results = self.run_tools(resp["tool_calls"], node)
                except Exception:  # noqa: BLE001
                    results = None
                if not results or len(results) != len(resp["tool_calls"]):
                    code = "HERRAMIENTA_NO_EJECUTADA"
            cost += float(resp.get("cost_usd", 0) or 0)            # TODOS los intentos cuestan: el tope de costo debe verlos
            if code != "MODEL_ERROR":
                self.profile.record(m, l, code == "OK")
            tried.append({"model": m, "layout": l, "task_sha": sha, "code": code})
            if self.on_event:
                self.on_event("dispatch_attempt", {"node": node["id"], "model": m, "layout": l, "code": code})
            if code == "OK":
                self.last[node["id"]] = (m, l)
                return {"ok": True, "model": m, "layout": l, "response": resp, "tool_results": results, "attempts": tried, "cost_usd": cost}
        return {"ok": False, "attempts": tried, "state": "blocked_with_evidence", "cost_usd": cost}

    def report(self, node_id, passed: bool):
        """Llamar cuando los checks del nodo FALLAN: la combinacion que 'actuo' pero no resolvio cuenta como fallo."""
        if not passed and node_id in self.last:
            self.profile.record(*self.last[node_id], False)

    def make_executor(self, gobernanza, build_task=default_task):
        def executor(node, ctx):
            flags = ctx.get("flags", {})
            excl = [self.last[node["id"]]] if node["id"] in self.last and (
                flags.get("force_different") or flags.get("switch_executor") or flags.get("switch_model_tier")) else []
            res = self.execute(node, gobernanza, build_task(node, ctx), exclude=excl)
            return {"output": (res.get("response") or {}).get("text", ""),
                    "actions": res.get("tool_results") or [], "dispatch": res["attempts"],
                    "cost_usd": res["cost_usd"]}
        return executor

    def event_hook(self, downstream=None):
        def hook(name, d):
            if name == "node_failed":
                self.report(d["node"], False)
            if downstream:
                downstream(name, d)
        return hook
