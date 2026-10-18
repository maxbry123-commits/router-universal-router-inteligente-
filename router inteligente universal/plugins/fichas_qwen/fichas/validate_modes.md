#!/usr/bin/env python3
"""Validador determinista FAIL-CLOSED de modes_registry.json y research_sources.json.
Sin dependencias externas.
Uso:  python3 validate_modes.py [modes_registry.json] [research_sources.json] [--strict]
--strict: ademas falla si quedan placeholders '<EDITAR' sin llenar (usalo despues de integrar)."""
import json, re, sys

EFFORTS = {"none", "low", "medium", "high", "xhigh"}
TOOL_CHOICES = {"auto", "required", "none"}
RESEARCH_MODES = {"none", "on_demand", "initial", "before_every_step", "dedicated"}
GUARDS = {"objective_pinned", "drift_guard", "anti_repeat", "evidence_required", "additive_only",
          "branch_only", "verbatim_input_immutable", "orchestrator_never_writes_code"}
WRITE_TOOLS = {"edit_file", "bash", "write_file"}
BASE_MODES = {None, "agent_code", "orchestrator"}
LIMIT_KEYS = ["max_iterations", "max_wall_clock_s", "max_cost_usd", "max_consecutive_no_progress", "max_tokens_per_turn"]
MODE_REQUIRED = ["id", "order", "slash", "label", "icon", "category", "summary", "base_mode", "autonomous_loop",
                 "no_escalation", "auto_eligible", "reasoning", "tool_choice", "tools_profile", "pipeline",
                 "research", "parallel", "limits", "outputs", "termination", "guards", "prompt_block", "prompt_import_slot"]
TOP_REQUIRED = ["registry_version", "selector", "ui", "hard_limit_caps", "immutable_sections", "self_modification",
                "objective_schema", "autonomy_rules", "tools_profiles", "step_catalog", "auto_classifier", "events", "modes"]

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def validate_registry(reg, strict=False):
    e = []
    for k in TOP_REQUIRED:
        if k not in reg:
            e.append(f"top: falta '{k}'")
    if e:
        return e
    sel = reg["selector"]
    if sel.get("precedence") != ["button_lock", "slash_command", "auto_classifier", "default_mode"]:
        e.append("selector: precedence debe ser button_lock>slash_command>auto_classifier>default_mode")
    if sel.get("on_unknown_mode") != "REJECT":
        e.append("selector: on_unknown_mode debe ser REJECT (fail-closed)")
    if sel.get("ui_thinking_toggle_policy") != "mode_wins":
        e.append("selector: ui_thinking_toggle_policy debe ser mode_wins")
    if not sel.get("gate", {}).get("trigger_words"):
        e.append("selector: gate.trigger_words vacio")
    modes = reg["modes"]
    ids = [m.get("id") for m in modes]
    if len(ids) != len(set(ids)):
        e.append("modes: ids duplicados")
    byid = {m.get("id"): m for m in modes}
    slashes = [m.get("slash") for m in modes]
    if len(slashes) != len(set(slashes)):
        e.append("modes: slash duplicados")
    if sel.get("auto_slash") in slashes:
        e.append("selector: auto_slash colisiona con un slash de modo")
    orders = sorted(m.get("order", -1) for m in modes)
    if orders != list(range(1, len(modes) + 1)):
        e.append("modes: order debe ser 1..N contiguo")
    if sorted(reg["ui"].get("menu_order", [])) != sorted(ids):
        e.append("ui: menu_order debe contener todos los modos exactamente una vez")
    dm = byid.get(sel.get("default_mode"))
    if dm is None:
        e.append("selector: default_mode no existe")
    elif dm.get("autonomous_loop"):
        e.append("selector: default_mode no puede ser autonomo")
    caps = reg["hard_limit_caps"]
    for k in LIMIT_KEYS + ["max_running", "max_cycle_repeats"]:
        if k not in caps:
            e.append(f"hard_limit_caps: falta {k}")
    steps = {s["id"] for s in reg["step_catalog"]}
    if len(steps) != len(reg["step_catalog"]):
        e.append("step_catalog: ids duplicados")
    for s in reg["step_catalog"]:
        if not s.get("evidence"):
            e.append(f"step_catalog: {s.get('id')} sin 'evidence' (PASS sin evidencia prohibido)")
    profiles = reg["tools_profiles"]
    for m in modes:
        mid = m.get("id", "?")
        miss = [k for k in MODE_REQUIRED if k not in m]
        if miss:
            e.append(f"{mid}: faltan campos {miss}")
            continue
        if not m["slash"].startswith("/"):
            e.append(f"{mid}: slash debe empezar con /")
        if m["base_mode"] not in BASE_MODES:
            e.append(f"{mid}: base_mode invalido")
        for ph in ("plan", "execute", "verify"):
            if m["reasoning"].get(ph) not in EFFORTS:
                e.append(f"{mid}: reasoning.{ph} invalido")
            if m["tool_choice"].get(ph) not in TOOL_CHOICES:
                e.append(f"{mid}: tool_choice.{ph} invalido")
            if m["tool_choice"].get(ph) == "required" and m["reasoning"].get(ph) != "none":
                e.append(f"{mid}: tool_choice.{ph}=required exige reasoning.{ph}=none")
        if m["tools_profile"] not in profiles:
            e.append(f"{mid}: tools_profile '{m['tools_profile']}' no existe")
        # pipeline
        flat = []
        for it in m["pipeline"]:
            if isinstance(it, str):
                flat.append(it)
            elif isinstance(it, dict):
                cyc = it.get("cycle")
                if not cyc or not isinstance(cyc, list):
                    e.append(f"{mid}: elemento de pipeline invalido {it}")
                    continue
                if not isinstance(it.get("max"), int) or not (1 <= it["max"] <= caps["max_cycle_repeats"]):
                    e.append(f"{mid}: cycle.max fuera de 1..{caps['max_cycle_repeats']}")
                if it.get("until") != "gap_list_empty":
                    e.append(f"{mid}: cycle.until debe ser gap_list_empty")
                flat.extend(cyc)
            else:
                e.append(f"{mid}: elemento de pipeline invalido")
        for s in flat:
            if s not in steps:
                e.append(f"{mid}: paso '{s}' no esta en step_catalog")
        # limites
        lim = m["limits"]
        for k in LIMIT_KEYS:
            if not isinstance(lim.get(k), (int, float)) or lim[k] <= 0:
                e.append(f"{mid}: limits.{k} faltante o no positivo")
            elif lim[k] > caps[k]:
                e.append(f"{mid}: limits.{k}={lim[k]} supera el tope duro {caps[k]}")
        if lim.get("on_limit") != "TERMINATE_WITH_REPORT":
            e.append(f"{mid}: limits.on_limit debe ser TERMINATE_WITH_REPORT")
        # paralelo
        p = m["parallel"]
        if p.get("max_running", 0) > caps["max_running"]:
            e.append(f"{mid}: parallel.max_running supera el tope {caps['max_running']}")
        if p.get("enabled") and p.get("overflow") != "queue":
            e.append(f"{mid}: parallel habilitado exige overflow=queue")
        # research
        r = m["research"]
        if r.get("mode") not in RESEARCH_MODES:
            e.append(f"{mid}: research.mode invalido")
        elif r["mode"] != "none":
            for k in ("sources_file", "log_to"):
                if not r.get(k):
                    e.append(f"{mid}: research.{k} requerido")
        if r.get("mode") == "before_every_step" and "research_before_step" not in flat:
            e.append(f"{mid}: before_every_step exige el paso research_before_step")
        if r.get("mode") == "dedicated" and "research_sources" not in flat:
            e.append(f"{mid}: dedicated exige el paso research_sources")
        # guards
        g = set(m["guards"])
        if not g <= GUARDS:
            e.append(f"{mid}: guards invalidos {sorted(g - GUARDS)}")
        if m["autonomous_loop"]:
            if not m["no_escalation"]:
                e.append(f"{mid}: modo autonomo requiere no_escalation=true")
            if m["auto_eligible"]:
                e.append(f"{mid}: modo autonomo no puede ser auto_eligible (solo boton/slash)")
            if m["pipeline"][0] != "pin_objective":
                e.append(f"{mid}: modo autonomo debe empezar con pin_objective")
            if "final_gate" not in flat:
                e.append(f"{mid}: modo autonomo debe incluir final_gate")
            need = {"objective_pinned", "drift_guard", "anti_repeat", "evidence_required"}
            if not need <= g:
                e.append(f"{mid}: modo autonomo requiere guards {sorted(need - g)}")
            if m["base_mode"] is None:
                e.append(f"{mid}: modo autonomo requiere base_mode")
        # orquestador nunca escribe codigo
        tools = set(profiles.get(m["tools_profile"], []))
        if m["base_mode"] == "orchestrator" or "orchestrator_never_writes_code" in g:
            if tools & WRITE_TOOLS:
                e.append(f"{mid}: orquestador con herramientas de escritura {sorted(tools & WRITE_TOOLS)}")
            if "orchestrator_never_writes_code" not in g:
                e.append(f"{mid}: orquestador requiere guard orchestrator_never_writes_code")
        # self-evolve
        if "branch_only" in g:
            if "additive_only" not in g:
                e.append(f"{mid}: branch_only requiere additive_only")
            sm = reg["self_modification"]
            if sm.get("merge_policy") != "pr_only":
                e.append("self_modification: merge_policy debe ser pr_only")
            if not str(sm.get("branch_prefix", "")).endswith("/"):
                e.append("self_modification: branch_prefix debe terminar en /")
            if not sm.get("require_tests_green"):
                e.append("self_modification: require_tests_green debe ser true")
        if m.get("id") and "verbatim_input_immutable" in g and "data_protection" not in m:
            e.append(f"{mid}: verbatim_input_immutable requiere data_protection")
        if m["prompt_import_slot"] is not None and not isinstance(m["prompt_import_slot"], str):
            e.append(f"{mid}: prompt_import_slot debe ser null o ruta (string)")
        if m.get("handoff_to") and m["handoff_to"] not in byid:
            e.append(f"{mid}: handoff_to apunta a modo inexistente")
    # clasificador
    ac = reg["auto_classifier"]
    rids = [r.get("id") for r in ac.get("rules", [])]
    if len(rids) != len(set(rids)):
        e.append("auto_classifier: ids de regla duplicados")
    for r in ac.get("rules", []):
        try:
            re.compile(r["pattern"])
        except Exception as ex:
            e.append(f"auto_classifier: regex invalida en {r.get('id')}: {ex}")
        tm = byid.get(r.get("then_mode"))
        if tm is None:
            e.append(f"auto_classifier: {r.get('id')} apunta a modo inexistente")
        elif not tm.get("auto_eligible"):
            e.append(f"auto_classifier: {r.get('id')} apunta a modo no auto_eligible {tm['id']}")
    # objetivo
    os_ = reg["objective_schema"]
    if not os_.get("required"):
        e.append("objective_schema: required vacio")
    # inmutables resuelven
    for path in reg["immutable_sections"]:
        cur = reg
        ok = True
        for k in path.split("."):
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if not ok:
            e.append(f"immutable_sections: ruta inexistente {path}")
    if strict:
        raw = json.dumps(reg, ensure_ascii=False)
        if "<EDITAR" in raw:
            e.append("strict: quedan placeholders <EDITAR ...> sin llenar en self_modification.targets")
    return e

def validate_sources(src):
    e = []
    s = src.get("sources", [])
    if len(s) != 20:
        e.append(f"sources: se esperaban 20 fuentes, hay {len(s)}")
    if len({x.get("id") for x in s}) != len(s):
        e.append("sources: ids duplicados")
    if len({x.get("domain") for x in s}) != len(s):
        e.append("sources: dominios duplicados")
    for x in s:
        for k in ("id", "domain", "kind", "use_for", "query_hint"):
            if not x.get(k):
                e.append(f"sources: {x.get('id', '?')} sin '{k}'")
    mn = src.get("min_successful")
    if not isinstance(mn, int) or not (1 <= mn <= len(s)):
        e.append("sources: min_successful invalido")
    if src.get("protocol", {}).get("fail_soft") is not True:
        e.append("sources: protocol.fail_soft debe ser true")
    return e

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    reg_p = args[0] if len(args) > 0 else "modes_registry.json"
    src_p = args[1] if len(args) > 1 else "research_sources.json"
    errs = validate_registry(load(reg_p), strict=strict) + validate_sources(load(src_p))
    if errs:
        print("VEREDICTO: FAIL")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("VEREDICTO: PASS (registro de modos + fuentes verificados" + (", strict" if strict else "") + ")")

if __name__ == "__main__":
    main()
