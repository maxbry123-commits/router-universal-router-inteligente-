#!/usr/bin/env python3
"""validate_2e.py — Validacion determinista de la Salida 2E (MINIMAX 4).

TODO es OFFLINE y de SOLO LECTURA: no escribe en Hugging Face, no llama a la
API de HF y no toca el repo (los artefactos temporales van a un directorio
temporal del sandbox).

Salida: una linea por check + resumen. Codigo 0 = todo PASS.
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


def check(name, fn):
    try:
        detail = fn()
        RESULTS.append((name, "PASS", detail or ""))
    except Exception as e:
        RESULTS.append((name, "FAIL", f"{type(e).__name__}: {e}"))


def sh(cmd, cwd=None, env=None):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run(cmd, shell=True, cwd=cwd or str(REPO), capture_output=True,
                          text=True, env=e)


# ── V1 imports reales de los modulos tocados ────────────────────────────────
def v1_imports():
    e = dict(os.environ)
    e["PYTHONPATH"] = str(REPO)
    e["CHECKPOINT_DIR"] = tempfile.mkdtemp(prefix="2e-ck-")
    e["PENDING_SYNC_DIR"] = tempfile.mkdtemp(prefix="2e-sync-")
    code = (
        "import router_llm_hf, router_llm_hf.loop_engine, router_llm_hf.harness_wiring, "
        "router_llm_hf.agent_router, router_llm_hf.chat_a_architect, "
        "router_llm_hf.chat_b_implementer, router_llm_hf.chat_ab_orchestrator, "
        "external.core.storage_wiring as sw; "
        "print('IMPORTS_OK', bool(sw.StorageWiring))"
    )
    r = sh(f"{sys.executable} -B -c \"{code}\"", env=e)
    if "IMPORTS_OK" not in r.stdout:
        raise RuntimeError((r.stdout + r.stderr)[-400:])
    return "8 modulos importan"


# ── V2 motor del loop: CLI ok + rc=2 en entrada mala ───────────────────────
def v2_loop_cli():
    e = dict(os.environ)
    e["PYTHONPATH"] = str(REPO)
    e["CHECKPOINT_DIR"] = tempfile.mkdtemp(prefix="2e-ck-")
    payload = json.dumps({"input": "genera una funcion python", "iteration": 1,
                          "max_iterations": 2, "task_id": "t1"})
    r = sh(f'{sys.executable} -B -m router_llm_hf.loop_engine \'{payload}\'', env=e)
    if r.returncode != 0:
        raise RuntimeError(f"rc={r.returncode} {r.stderr[-300:]}")
    data = json.loads(r.stdout)
    if "done" not in data or data.get("engine") is None and "plan" not in data:
        raise RuntimeError(f"contrato roto: {str(data)[:200]}")
    if data.get("done") is not False:
        raise RuntimeError(f"en la iteracion 1 de 2 no deberia estardone: {str(data)[:160]}")
    # Ultima iteracion -> done True (el loop termina).
    last = json.dumps({"input": "genera una funcion python", "iteration": 2,
                       "max_iterations": 2, "task_id": "t1"})
    r2 = sh(f'{sys.executable} -B -m router_llm_hf.loop_engine \'{last}\'', env=e)
    d2 = json.loads(r2.stdout)
    if d2.get("done") is not True:
        raise RuntimeError(f"en la ultima iteracion deberia estar done: {str(d2)[:160]}")
    bad = sh(f'{sys.executable} -B -m router_llm_hf.loop_engine \'{{no-json}}\'', env=e)
    if bad.returncode != 2:
        raise RuntimeError(f"entrada invalida deberia dar rc=2, dio {bad.returncode}")
    return (f"iter1 done={data['done']} iter2 done={d2['done']} "
            f"mode={data['mode']} adapter={data.get('adapter_mode')} rc_malo={bad.returncode}")


# ── V3 determinismo: misma entrada -> mismo resultado ──────────────────────
def v3_determinismo():
    e = dict(os.environ)
    e["PYTHONPATH"] = str(REPO)
    e["CHECKPOINT_DIR"] = tempfile.mkdtemp(prefix="2e-ck-")
    payload = json.dumps({"input": "audita este codigo python", "iteration": 2, "task_id": "t2"})
    outs = []
    for _ in range(2):
        r = sh(f'{sys.executable} -B -m router_llm_hf.loop_engine \'{payload}\'', env=e)
        outs.append(r.stdout.strip())
    if outs[0] != outs[1]:
        raise RuntimeError("dos ejecuciones difieren")
    return "2 ejecuciones identicas (byte a byte)"


# ── V4 proxy: rutas nuevas presentes ───────────────────────────────────────
def v4_rutas():
    src = (REPO / "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py").read_text(encoding="utf-8")
    need = ['/v1/agents/{agent_name}', '/v1/openclaw', '/v1/hermes', '/harness/health',
            '@app.get("/v1/agents")', '/v1/loop/resume', '/v1/loop/step']
    missing = [n for n in need if n not in src]
    if missing:
        raise RuntimeError(f"faltan rutas: {missing}")
    return f"{len(need)} rutas verificadas"


# ── V5 proxy: import real + rutas registradas ──────────────────────────────
def v5_proxy_import():
    e = dict(os.environ)
    e["ROUTER_API_KEY"] = "dummy-2e"
    e["PYTHONPATH"] = str(REPO)
    code = (
        "import importlib.util,sys,os;"
        "p=os.path.join('ROUTER MVP v1','system_prompt_py','openai_compatible_proxy.py');"
        "spec=importlib.util.spec_from_file_location('proxy_2e',p);"
        "m=importlib.util.module_from_spec(spec);sys.modules['proxy_2e']=m;"
        "spec.loader.exec_module(m);"
        "rs={r.path for r in m.app.routes};"
        "print('ROUTES', len(rs));"
        "print('HAS_AGENTS', '/v1/agents/{agent_name}' in rs);"
        "print('HAS_HARNESS', '/harness/health' in rs)"
    )
    r = sh(f'{sys.executable} -B -c "{code}"', env=e)
    if "HAS_AGENTS True" not in r.stdout or "HAS_HARNESS True" not in r.stdout:
        raise RuntimeError((r.stdout + r.stderr)[-500:])
    return r.stdout.strip().replace("\n", " ")


# ── V6 registro de agentes + espejo ────────────────────────────────────────
def v6_agentes():
    from router_llm_hf.agent_router import (
        get_agents_with_mirror, get_all_active_agents, load_registry, route_task,
    )
    reg = load_registry().get("agents", {})
    if len(reg) != 4:
        raise RuntimeError(f"esperaba 4 agentes, hay {len(reg)}")
    for name, data in reg.items():
        if not data.get("mirror_endpoint"):
            raise RuntimeError(f"{name} sin espejo")
        if not data.get("chat_path"):
            raise RuntimeError(f"{name} sin chat_path")
    if route_task("openclaw", use_mirror=True) != reg["openclaw"]["mirror_endpoint"]:
        raise RuntimeError("route_task no devuelve el espejo")
    return (f"4 agentes · activos={len(get_all_active_agents())} "
            f"con_espejo={len(get_agents_with_mirror())}")


# ── V7 memoria: checkpoint a un bucket hf:// -> cola local, no falso OK ─────
def v7_memoria():
    import asyncio
    from router_llm_hf.harness_wiring import HarnessClient
    tmp = tempfile.mkdtemp(prefix="2e-sync-")
    os.environ["PENDING_SYNC_DIR"] = tmp
    os.environ["MCP_MEMORY_URL"] = "hf://buckets/COMAND-CENTER-1/yaiwes-memoria-storage"
    os.environ.pop("MCP_MEMORY_HTTP_URL", None)
    c = HarnessClient()
    res = asyncio.run(c.send_checkpoint({"model": "x", "messages": []}))
    if res.get("synced") is not False or res.get("stored") != "local_pending_sync":
        raise RuntimeError(f"recibo inesperado: {res}")
    if not os.path.exists(res["path"]):
        raise RuntimeError("no se encolo el checkpoint")
    return f"encolado en {os.path.basename(res['path'])} (synced=False, sin falso OK)"


# ── V8 harness: fallback de clave (la mejora m3 lo habia roto) ──────────────
def v8_harness_clave():
    import asyncio
    from router_llm_hf import harness_wiring
    os.environ.pop("HARNESS_KEY", None)
    os.environ["ROUTER_API_KEY"] = "dummy-2e"
    os.environ["AGENT_HARNESS_URL"] = "http://127.0.0.1:9/no-existe"
    try:
        asyncio.run(harness_wiring.call_harness({"messages": []}))
    except RuntimeError as e:
        if "no configurada" in str(e):
            raise RuntimeError(f"sigue fallando por clave: {e}")
        return "usa ROUTER_API_KEY (fallo real de red, no de configuracion)"
    raise RuntimeError("call_harness deberia fallar (no hay servidor)")


# ── V9 almacenamiento: el adaptador NO crea nada ───────────────────────────
def v9_storage():
    src = (REPO / "external/core/storage_wiring.py").read_text(encoding="utf-8")
    # Se miran LLAMADAS REALES (arbol AST), no la prosa del docstring.
    import ast

    tree = ast.parse(src)
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                called.add(fn.attr)
            elif isinstance(fn, ast.Name):
                called.add(fn.id)
            for kw in node.keywords:
                if kw.arg == "repo_type" and getattr(kw.value, "value", None) == "bucket":
                    raise RuntimeError("el adaptador sigue usando repo_type=bucket (invalido)")
    forbidden = called & {"create_repo", "upload_file", "upload_folder", "delete_repo",
                           "repo_info", "delete_file"}
    if forbidden:
        raise RuntimeError(f"el adaptador sigue escribiendo/leyendo el bucket por API: {sorted(forbidden)}")
    if "HfApi" in called:
        raise RuntimeError("el adaptador sigue usando el cliente del hub (repo_type bucket no existe)")
    from external.core.storage_wiring import StorageWiring
    res = StorageWiring.ensure_bucket()
    if res.get("status") in (None, ""):
        raise RuntimeError(f"respuesta sin status: {res}")
    return f"status={res.get('status')} (sin escrituras)"


# ── V10 sonda de reinicio: inventario local, sin llamadas a HF ─────────────
def v10_sonda():
    r = sh(f"{sys.executable} -B scripts/hf_restart_space.py --list")
    if r.returncode != 0:
        raise RuntimeError((r.stdout + r.stderr)[-300:])
    n = sum(1 for line in r.stdout.splitlines() if "group=" in line)
    if n != 6:
        raise RuntimeError(f"inventario con {n} Spaces, esperaba 6")
    src = (REPO / "scripts/hf_restart_space.py").read_text(encoding="utf-8")
    if "create_repo" in src or "delete" in src:
        raise RuntimeError("la sonda crea o borra algo")
    return f"{n} Spaces en el inventario (sin llamadas a HF)"


# ── V11 front: puente del chat + espejo en los paneles + selector ─────────
def v11_front():
    chat = (REPO / "chat-router/chat/index.html").read_text(encoding="utf-8")
    sel = (REPO / "chat-router/chat/ui/model-selector.js").read_text(encoding="utf-8")
    oc = (REPO / "chat-router/chat/ui/openclaw-panel.html").read_text(encoding="utf-8")
    he = (REPO / "chat-router/chat/ui/hermes-panel.html").read_text(encoding="utf-8")
    if "window.chatBridge" not in chat or "sendToAgent" not in chat:
        raise RuntimeError("falta el puente del chat")
    if "/v1/agents/" not in sel or "router:" not in sel and "MODEL_GROUPS.router" not in sel:
        raise RuntimeError("el selector no expone router ni agentes")
    for name, src in (("openclaw", oc), ("hermes", he)):
        if "sendToAgent" not in src or "chatBridge" not in src:
            raise RuntimeError(f"el panel {name} no tiene espejo")
    r = sh("node --version")
    node = r.stdout.strip()
    for js in ("chat-router/chat/ui/model-selector.js", "chat-router/chat/ui/ui-controller.js"):
        tmp = tempfile.mkdtemp(prefix="2e-js-")
        target = os.path.join(tmp, "check.mjs")
        Path(target).write_text((REPO / js).read_text(encoding="utf-8"), encoding="utf-8")
        c = sh(f"node --check {target}")
        if c.returncode != 0:
            raise RuntimeError(f"{js}: {c.stderr[-200:]}")
    return f"chat+2 paneles+selector OK (node {node})"


# ── V12 regresion: los 6 V de la Salida 2D siguen verdes ───────────────────
def v12_regresion():
    e = dict(os.environ)
    e["PYTHONPATH"] = str(REPO)
    e["CHECKPOINT_DIR"] = tempfile.mkdtemp(prefix="2e-ck-")
    checks = [
        ("V1_IMPORTS_OK", "import external.tools.fs_tools, router_llm_hf.sandbox, external.tools.shell_tool, external.tools.tool_registry, external.tools.verify_tool, external.core.context_manager, external.core.semantic_cache, external.history.conversation_store, external.memory.long_term, external.core.health_check; print('V1_IMPORTS_OK')"),
        ("V2_REGISTRY_OK", "from external.tools.tool_registry import REGISTRY; assert len(REGISTRY.list())>=10; print('V2_REGISTRY_OK')"),
        # Contrato actual (tras fusionar los modos de servicio del sibling):
        # VALID_MODES = 12 modos de codigo + 4 de servicio + python/backend/agentic_tool.
        ("V6_MODES_OK", "from router_llm_hf.mode_router import VALID_MODES as V; from router_llm_hf.mode_detector import RULES, SERVICE_MODE_NAMES; need=set(RULES)|set(SERVICE_MODE_NAMES)|{'python','backend','agentic_tool'}; assert need<=set(V), sorted(need-set(V)); print('V6_MODES_OK', len(V))"),
        # El filtro de modos sigue vivo: un modo inexistente se rechaza.
        ("V6B_INVALID_MODE_OK", "from router_llm_hf.mode_router import route; r=route({'mode':'modo_que_no_existe'}); assert 'invalid_mode' in str(r.get('error')), r; print('V6B_INVALID_MODE_OK')"),
    ]
    out = []
    for name, code in checks:
        r = sh(f'{sys.executable} -B -c "{code}"', env=e)
        if name not in r.stdout:
            raise RuntimeError(f"{name} fallo: {(r.stdout + r.stderr)[-200:]}")
        out.append(name)
    proxy = (REPO / "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py").read_text(encoding="utf-8")
    if "/v1/loop/resume" not in proxy:
        raise RuntimeError("V3/V4: falta /v1/loop/resume")
    loopjs = (REPO / "chat-router/chat/ui/loop.js").read_text(encoding="utf-8")
    if "resumeLoop" not in loopjs:
        raise RuntimeError("V4: falta resumeLoop")
    return " + ".join(out + ["V3_OK", "V4_OK"])


def main():
    check("V2E_01_IMPORTS", v1_imports)
    check("V2E_02_LOOP_CLI", v2_loop_cli)
    check("V2E_03_LOOP_DETERMINISTA", v3_determinismo)
    check("V2E_04_RUTAS_PROXY", v4_rutas)
    check("V2E_05_PROXY_IMPORT", v5_proxy_import)
    check("V2E_06_AGENTES_ESPEJO", v6_agentes)
    check("V2E_07_MEMORIA_COLA", v7_memoria)
    check("V2E_08_HARNESS_CLAVE", v8_harness_clave)
    check("V2E_09_STORAGE_SIN_ESCRITURAS", v9_storage)
    check("V2E_10_SONDA_RESTART", v10_sonda)
    check("V2E_11_FRONT_ESPEJO", v11_front)
    check("V2E_12_REGRESION_2D", v12_regresion)

    width = max(len(r[0]) for r in RESULTS)
    for name, status, detail in RESULTS:
        print(f"{name:<{width}}  {status:<4}  {detail}")
    fails = [r for r in RESULTS if r[1] != "PASS"]
    print(f"\nTOTAL {len(RESULTS) - len(fails)}/{len(RESULTS)} PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
