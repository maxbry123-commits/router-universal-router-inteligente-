#!/usr/bin/env python3
"""Validador determinista v1.1 (aditivo; reutiliza validate_contract.py).
Uso: python3 validate_contract_v11.py loop_contract.example.v1_1.json"""
import sys
import validate_contract as base

EFFORT_NONE = "none"

def v11_errors(doc):
    errs = []
    ids = {n["id"] for n in doc["dag"]["nodes"]}
    rp, ap, ar, ia, tp = (doc["reasoning_policy"], doc["autonomy_policy"], doc["anti_repeat_guard"],
                          doc["instruction_adherence"], doc["tool_policy"])
    for ph in ("plan", "execute", "verify"):
        if rp["tool_choice_by_phase"][ph] in ("required",) and rp["by_phase"][ph] != EFFORT_NONE:
            errs.append(f"v11: fase {ph} usa tool_choice=required con thinking activo (el modelo puede omitir la llamada)")
    if ap["max_consecutive_reads"] > 5:
        errs.append("v11: max_consecutive_reads > 5 favorece el bucle de lectura")
    if ar["dedupe_tool_calls"]["max_identical"] >= ar["dedupe_tool_calls"]["window"]:
        errs.append("v11: dedupe max_identical debe ser menor que window")
    kinds = {t["kind"] for t in tp["tools"]}
    if not ({"read"} <= kinds and ({"write", "exec"} & kinds)):
        errs.append("v11: tool_policy debe incluir herramientas de lectura Y de escritura/ejecucion")
    rs = doc.get("research_policy", {})
    if rs.get("enabled") and not ({"search", "fetch"} & kinds):
        errs.append("v11: research_policy activo pero tool_policy no tiene search/fetch")
    for pt in doc.get("review_points", []):
        if pt["after_node"] not in ids:
            errs.append(f"v11: review_point {pt['id']} apunta a nodo inexistente {pt['after_node']}")
        if pt["kind"] not in ap["allowed_pause_points"]:
            errs.append(f"v11: review_point {pt['id']} tipo {pt['kind']} no esta en allowed_pause_points")
    if not ia["drift_guard"]["allowed_globs"]:
        errs.append("v11: drift_guard sin allowed_globs")
    for n in doc["dag"]["nodes"]:
        for c in n["acceptance"]:
            pass
    st = doc.get("harness_selftest", {})
    if st.get("enabled"):
        kinds_t = {c["assert"]["kind"] for c in st["cases"]}
        need = {"tool_result_visible_next_turn", "no_repeated_question", "acts_within_n_turns"}
        if not need <= kinds_t:
            errs.append(f"v11: selftest debe cubrir {sorted(need - kinds_t)}")
    return errs

def main():
    if len(sys.argv) < 2:
        print("FAIL: falta ruta del contrato"); sys.exit(1)
    doc = base.load(sys.argv[1])
    errs = []
    try:
        schema = base.load("loop_contract.schema.v1_1.json")
        se = base.schema_errors(doc, schema)
    except Exception as e:
        se = [f"schema: {e}"]
    errs += se
    structural = base.dag_errors(doc) + base.router_errors(doc) + base.loop_errors(doc) + v11_errors(doc)
    if se and all("jsonschema no instalado" in s for s in se):
        errs = se  # fail-closed pero seguimos mostrando reglas estructurales
    errs += structural
    if errs:
        print("VEREDICTO: FAIL")
        for e in errs: print(" -", e)
        sys.exit(1)
    print("VEREDICTO: PASS (esquema v1.1 + DAG + router + bucle + autonomia verificados)")

if __name__ == "__main__":
    main()
