#!/usr/bin/env python3
"""validate_2f.py — MINIMAX 2F · validador fail-closed (13 checks).

Comprueba lo que el Director pidio:
  1. Registro v3 con los 6 agentes (incluidos ruflo y rowboat) y su interruptor.
  2. Estado ON/OFF persistente por agente (round-trip real en disco).
  3. Historial y memoria por agente (round-trip real).
  4. Enrutado: agente OFF no enruta; agente ON enruta a su espejo.
  5. El proxy IMPORTA de verdad y registra las rutas nuevas.
  6. No hay rutas duplicadas (/v1/agents y /v1/modes, una sola vez).
  7. Clasificador + parse del bloque 📌 (F2 literal del Director).
  8. Render F3/F4 con Mapa Mental y botonera.
  9. Handoff dual-output (prosa + JSON delimitado) ida y vuelta.
 10. Bitacora append-only con taint.
 11. Chat: 4 ventanas nuevas + botonera + render NCT + selector con 6 agentes.
 12. Auto-pull de las 3 raices (informe, sin escribir).
 13. Prueba FUNCIONAL del proxy (TestClient) si hay fastapi+httpx.

Salida: una linea por check. RC 0 solo si TODOS pasan.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

RESULTS = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'} · {name}" + (f" · {detail}" if detail else ""))
    return bool(ok)


def main() -> int:
    # Si falta fastapi, se reintenta con el venv de infraestructura.
    try:
        import fastapi  # noqa: F401
    except Exception:
        venv = Path("/workspace/.venv-infra/bin/python")
        if venv.exists() and venv != Path(sys.executable):
            print(f"NOTA: se reintenta con {venv} (falta fastapi en el interprete actual)")
            os.execv(str(venv), [str(venv), str(Path(__file__).resolve()), *sys.argv[1:]])
        check("entorno: fastapi disponible", False, "no hay fastapi ni venv de infraestructura")
        return 1

    # ── V1 · registro v3 ───────────────────────────────────────────────────
    reg = json.loads((REPO / "router_llm_hf" / "AGENTS_REGISTRY.json").read_text(encoding="utf-8"))
    agents = reg.get("agents") or {}
    faltan = [n for n in ("openclaw", "hermes", "chat_a", "chat_b", "ruflo", "rowboat") if n not in agents]
    check("V1 registro: 6 agentes (ruflo y rowboat incluidos)", not faltan,
          f"faltan={faltan}" if faltan else f"version={reg.get('version')} agentes={len(agents)}")
    sin_memoria = [n for n, a in agents.items() if not (a.get("memory") or {}).get("history")]
    check("V1b registro: cada agente declara memoria e historial", not sin_memoria,
          f"sin memoria={sin_memoria}" if sin_memoria else "")
    check("V1c registro: 3 raices declaradas con auto_pull",
          len(reg.get("roots") or {}) == 3 and all(r.get("auto_pull") for r in (reg.get("roots") or {}).values()),
          f"raices={sorted((reg.get('roots') or {}).keys())}")

    # ── V2/V3 · estado ON/OFF + historial + memoria (round-trip real) ─────
    with tempfile.TemporaryDirectory(prefix="agentstate-") as tmp:
        os.environ["AGENT_STATE_DIR"] = tmp
        for mod in [m for m in list(sys.modules) if m.startswith("router_llm_hf")]:
            del sys.modules[mod]
        from router_llm_hf import agent_state as st

        st.set_enabled("ruflo", True, "test")
        ok_on = st.is_enabled("ruflo") is True
        st.set_enabled("ruflo", False, "test")
        ok_off = st.is_enabled("ruflo") is False
        check("V2 ON/OFF: se enciende y se apaga (persistido en disco)", ok_on and ok_off)

        st.append_turn("ruflo", "user", "hola", {"origen": "test"})
        st.append_turn("ruflo", "bot", "respuesta")
        hist = st.get_history("ruflo", limit=10)
        check("V3 historial: 2 turnos guardados y leidos en orden", len(hist) == 2 and hist[0]["role"] == "bot",
              f"turnos={len(hist)}")

        st.set_memory("ruflo", "objetivo", "cablear agentes")
        mem = st.get_memory("ruflo")
        check("V3b memoria: clave persistente por agente", mem.get("objetivo") == "cablear agentes",
              f"claves={sorted(st.memory_keys('ruflo'))}")

        # Enrutado con el interruptor.
        from router_llm_hf import agent_router as ar
        ar_off = ar.route_task("ruflo")
        st.set_enabled("ruflo", True, "test")
        ar_on = ar.route_task("ruflo")
        check("V4 enrutado: OFF no enruta / ON enruta al espejo", ar_off is None and bool(ar_on),
              f"off={ar_off} on={ar_on}")

        inv = ar.list_agents()
        check("V4b inventario: 6 agentes con interruptor y contadores",
              len(inv.get("agents") or {}) == 6 and "history_count" in inv["agents"]["ruflo"],
              f"agentes={sorted((inv.get('agents') or {}).keys())}")
    os.environ.pop("AGENT_STATE_DIR", None)

    # ── V5/V6 · proxy: import real + rutas ────────────────────────────────
    sys.path.insert(0, str(REPO / "ROUTER MVP v1" / "system_prompt_py"))
    os.environ["ROUTER_API_KEY"] = os.environ.get("ROUTER_API_KEY", "dummy-validate")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "proxy_2f", REPO / "ROUTER MVP v1" / "system_prompt_py" / "openai_compatible_proxy.py")
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    paths = [getattr(r, "path", "") for r in proxy.app.routes]
    requeridas = ["/v1/agents", "/v1/agents/{agent_name}/state", "/v1/agents/{agent_name}/history",
                  "/v1/agents/{agent_name}/memory", "/v1/artifacts", "/v1/artifacts/{name}",
                  "/v1/nct/parse", "/v1/nct/render", "/v1/nct/botonera", "/v1/nct/recovery",
                  "/v1/roots", "/v1/roots/pull"]
    faltan_r = [p for p in requeridas if p not in paths]
    check("V5 proxy: importa y registra todas las rutas nuevas", not faltan_r,
          f"faltan={faltan_r}" if faltan_r else f"rutas={len(paths)}")
    dup_agents = paths.count("/v1/agents")
    dup_modes = paths.count("/v1/modes")
    check("V6 proxy: sin rutas duplicadas (/v1/agents y /v1/modes)", dup_agents == 1 and dup_modes == 1,
          f"/v1/agents={dup_agents} /v1/modes={dup_modes}")

    # ── V7 · clasificador + parse del bloque 📌 ───────────────────────────
    from router_llm_hf import nct_format as nct
    k1 = nct.classify_input("refactoriza este codigo python y arregla el bug")["kind"]
    k2 = nct.classify_input("¿que hora es?")["kind"]
    k3 = nct.classify_input("audita el repositorio forense y busca gaps")["kind"]
    check("V7 clasificador: programacion / pregunta / auditoria",
          k1 == "programacion" and k2 == "pregunta" and k3 == "auditoria",
          f"{k1}/{k2}/{k3}")

    bloque = """# 🔵 F2 — INPUT LARGO · MODO AGÉNTICO / TOOL

**Objetivo:** cablear los 6 agentes al chat con interruptor ON/OFF

**MI INTERPRETACIÓN:**
- hay dos raices sin cablear
- falta memoria por agente
- falta auto-pull

**PREGUNTAS DE CLARIFICACIÓN (máx 3):**
1. ¿ruflo arranca en OFF?
2. ¿la memoria va al bucket?
3. ¿quien valida el deploy?

**PLAN PROPUESTO — requiere aprobación**
Micro-flujo horizontal:
ACCIÓN A → ACCIÓN B → REVISIÓN → REFACTORÍA → VALIDACIÓN

**Restricciones:** no escribir en HF
**Criterio de éxito:** 12/12 checks PASS

### PLANIFICACIÓN — pasos en orden estricto
1. registro → `router_llm_hf/AGENTS_REGISTRY.json`
2. estado → `router_llm_hf/agent_state.py`

### CRITERIOS DE EXITO
- [ ] registro con 6 agentes
- [ ] memoria por agente

### ARCHIVOS A MODIFICAR / CREAR
- `router_llm_hf/agent_state.py` (crear)
- `chat-router/chat/index.html` (modificar)

### ROLLBACK SI FALLA
```bash
git reset --hard HEAD~1
```
"""
    p = nct.parse_input_block(bloque)
    check("V7b parse 📌: objetivo + 3 preguntas + 2 criterios + 2 archivos + rollback",
          p.get("objetivo", "").startswith("cablear los 6 agentes")
          and len(p.get("preguntas") or []) == 3
          and len(p.get("criterios") or []) == 2
          and len(p.get("archivos") or []) == 2
          and "git reset" in (p.get("rollback") or ""),
          f"obj={bool(p.get('objetivo'))} preguntas={len(p.get('preguntas') or [])} "
          f"criterios={len(p.get('criterios') or [])} archivos={len(p.get('archivos') or [])}")

    # ── V8 · render F3/F4 + mapa mental + botonera ────────────────────────
    data = {"objetivo": "cablear agentes", "texto": "hecho", "estado": "STABLE", "progreso": "100%",
            "tiempo": "00:10:00", "pendientes": 0, "confirma_input": True, "instrucciones": True,
            "grupos": [{"name": "Chat", "done": 3, "total": 3, "piezas": [{"name": "selector", "actual": True}]}],
            "analisis": "a", "arquitectura": "b", "evidencias": ["V1..V12"], "plan": ["p1"], "codigo": "print(1)"}
    out3 = nct.render_output(data, "F3")
    out4 = nct.render_output(data, "F4")
    check("V8 render: F3 con botonera y F4 con mapa mental",
          "F3 — OUTPUT CORTO" in out3["markdown"] and "BOTONERA NCT/APEX" in out3["markdown"]
          and "F4 — OUTPUT LARGO" in out4["markdown"] and "VISIÓN GLOBAL PERFIL" in out4["markdown"]
          and "MADUREZ" in out4["markdown"],
          f"F3={len(out3['markdown'])}B F4={len(out4['markdown'])}B")

    # ── V9 · handoff dual-output ──────────────────────────────────────────
    h = nct.build_handoff(data)
    back = nct.parse_handoff(nct.render_handoff_block(h))
    check("V9 handoff: JSON delimitado ida y vuelta", back is not None and back.get("task_intent") == "cablear agentes",
          f"id={h.get('handoff_id') or 'auto'}")

    # ── V10 · bitacora append-only con taint ──────────────────────────────
    with tempfile.TemporaryDirectory(prefix="wall-") as tmp:
        os.environ["AGENT_STATE_DIR"] = tmp
        nct.crazy_wall_append({"event": "decision", "payload": {"x": 1}, "taint": "suspicious"})
        nct.crazy_wall_append({"event": "tool_call", "payload": {"y": 2}})
        wall = nct.crazy_wall_read(10)
        check("V10 bitacora: 2 eventos append-only con taint",
              len(wall) == 2 and wall[0]["event"] == "tool_call" and wall[0]["taint"] == "clean"
              and wall[1]["event"] == "decision" and wall[1]["taint"] == "suspicious",
              f"eventos={len(wall)} (wall[0]=mas nuevo)")
    os.environ.pop("AGENT_STATE_DIR", None)

    # ── V11 · frontend ────────────────────────────────────────────────────
    html = (REPO / "chat-router" / "chat" / "index.html").read_text(encoding="utf-8")
    sel = (REPO / "chat-router" / "chat" / "ui" / "model-selector.js").read_text(encoding="utf-8")
    faltan_w = [w for w in ("v-agentes", "v-input", "v-artefactos", "v-cuadros") if w not in html]
    check("V11 chat: 4 ventanas nuevas (agentes/input/artefactos/cuadros)", not faltan_w,
          f"faltan={faltan_w}" if faltan_w else "")
    check("V11b chat: botonera + render NCT en el envio + interruptor ON/OFF",
          'id="botonera"' in html and "/v1/nct/render" in html and "/state" in html)
    check("V11c selector: ruflo y rowboat con estado ON/OFF",
          "ruflo" in sel and "rowboat" in sel and "AGENTS_FALLBACK" in sel and "option.disabled" in sel)

    # ── V12 · auto-pull de las raices (informe, sin escribir) ─────────────
    proc = subprocess.run([sys.executable, str(REPO / "scripts" / "pull_agent_roots.py"), "--all", "--json"],
                          capture_output=True, text=True, timeout=180)
    ok_pull = proc.returncode == 0
    detalle = ""
    if ok_pull:
        try:
            data_pull = json.loads(proc.stdout)
            ok_pull = len(data_pull.get("roots") or {}) == 3
            detalle = "raices=" + ",".join(sorted((data_pull.get("roots") or {}).keys()))
        except Exception as exc:
            ok_pull = False
            detalle = str(exc)
    else:
        detalle = (proc.stderr or proc.stdout)[-200:]
    check("V12 auto-pull: informe de las 3 raices sin escribir", ok_pull, detalle)

    # ── V13 · prueba funcional del proxy (TestClient) ─────────────────────
    try:
        from fastapi.testclient import TestClient
        with tempfile.TemporaryDirectory(prefix="artifacts-") as tmp:
            os.environ["ARTIFACT_DIR"] = tmp
            os.environ["AGENT_STATE_DIR"] = tmp
            proxy.ARTIFACT_DIR = tmp  # el valor real se fija en el modulo, no en el entorno
            client = TestClient(proxy.app)
            KEY = {"x-api-key": getattr(proxy, "ROUTER_API_KEY", "dummy-validate")}
            r = client.get("/v1/agents")
            d = r.json() if r.content else {}
            nombres = sorted((d.get("agents") or {}).keys())
            ok13 = r.status_code == 200 and "ruflo" in nombres and "rowboat" in nombres
            r2 = client.post("/v1/artifacts", json={"name": "prueba.md", "kind": "md", "content": "# hola"}, headers=KEY)
            ok13 = ok13 and r2.status_code == 200 and r2.json().get("name") == "prueba.md"
            r3 = client.post("/v1/nct/parse", json={"text": bloque}, headers=KEY)
            ok13 = ok13 and r3.status_code == 200 and r3.json()["parsed"]["objetivo"].startswith("cablear")
            r4 = client.get("/v1/agents", headers=KEY)
            ok13 = ok13 and r4.status_code == 200
            check("V13 funcional: /v1/agents, /v1/artifacts y /v1/nct/parse responden bien", ok13,
                  f"agentes={nombres} artefacto={r2.status_code}")
    except Exception as exc:
        check("V13 funcional: TestClient del proxy", False, f"no ejecutable: {exc}")

    # ── RESUMEN ───────────────────────────────────────────────────────────
    fallos = [n for n, ok, _ in RESULTS if not ok]
    print(f"\nRESUMEN 2F: {len(RESULTS) - len(fallos)}/{len(RESULTS)} PASS")
    if fallos:
        for n in fallos:
            print(f"  FAIL: {n}")
        return 1
    print("VALIDACION 2F: TODO PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
