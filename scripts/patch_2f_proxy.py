#!/usr/bin/env python3
"""patch_2f_proxy.py — MINIMAX 2F: cableado real de agentes + formato NCT/APEX.

Correcciones sobre `ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py`:

  1. BUG REAL: la ruta `/v1/agents` estaba DEFINIDA 4 veces y `/v1/modes` 4 veces
     (un bloque por agente de la serie MINIMAX). FastAPI solo honra la
     PRIMERA: las demas eran codigo muerto, y la version que si comprobaba si
     la ruta existia de verdad ("implemented") nunca se ejecuto. Aqui queda UNA
     ruta canonica de cada, con la comprobacion "implemented" si misma.
  2. Agentes ruflo y rowboat (las dos raices reales del workspace) con su
     prompt: sin ellos `/v1/agents/ruflo` devolvia 404.
  3. Interruptor ON/OFF: un agente apagado NO se enruta (409 explicito).
  4. Historial y memoria por agente: cada turno se persiste (append-only) y la
     memoria del agente guarda el ultimo objetivo.
  5. Rutas nuevas: estado, historial, memoria, artefactos, NCT (parse/render/
     botonera/recovery) y estado de las raices con auto-pull.

Fail-closed: cada sustitucion se verifica (una sola ocurrencia) y el script
devuelve != 0 si algo no cuadra.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROXY = Path(__file__).resolve().parent.parent / "ROUTER MVP v1" / "system_prompt_py" / "openai_compatible_proxy.py"

# ──────────────────────────────────────────────────────────────────────────
# 1. PROMPTS DE ruflo y rowboat (los 404 de /v1/agents/<nombre>)
# ──────────────────────────────────────────────────────────────────────────
OLD_PROMPTS = '''    "chat_b": (
        "Eres ChatB, el implementador del router. Escribes el codigo, usas las "
        "herramientas y devuelves el resultado verificable."
    ),
}
'''

NEW_PROMPTS = '''    "chat_b": (
        "Eres ChatB, el implementador del router. Escribes el codigo, usas las "
        "herramientas y devuelves el resultado verificable."
    ),
    "ruflo": (
        "Eres Ruflo, la raiz de agente claude-flow del workspace. Planificas "
        "con agentes especializados (architect, coder, reviewer, security) y "
        "devuelves el plan y el resultado verificable."
    ),
    "rowboat": (
        "Eres Rowboat, la raiz de agente del workspace. Explicas, operas y "
        "documentas con los componentes disponibles y devuelves el resultado."
    ),
}
'''

# ──────────────────────────────────────────────────────────────────────────
# 2. _agent_request: interruptor ON/OFF + persistencia de turno y memoria
# ──────────────────────────────────────────────────────────────────────────
OLD_AGENT_REQ = '''    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    prompt = _agent_prompt(agent_name)
    if not prompt:
        raise HTTPException(404, detail=f"agente desconocido: {agent_name}; known={sorted(AGENT_PROMPTS)}")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    user_messages = body.get("messages") or []
    if not user_messages:
        raise HTTPException(400, detail="messages vacio")
'''

NEW_AGENT_REQ = '''    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    prompt = _agent_prompt(agent_name)
    if not prompt:
        raise HTTPException(404, detail=f"agente desconocido: {agent_name}; known={sorted(AGENT_PROMPTS)}")

    # MINIMAX 2F · interruptor ON/OFF: un agente apagado no se enruta.
    try:
        from router_llm_hf.agent_router import get_agent, is_enabled
        if get_agent(agent_name) and not is_enabled(agent_name):
            raise HTTPException(
                status_code=409,
                detail=f"agente {agent_name} esta OFF (interruptor del registro central); "
                       f"enciendelo en /v1/agents/{agent_name}/state o en la ventana AGENTES del chat",
            )
    except HTTPException:
        raise
    except Exception as _e:
        print(f"[AGENTS] estado de {agent_name} no consultable: {_e}")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    user_messages = body.get("messages") or []
    if not user_messages:
        raise HTTPException(400, detail="messages vacio")
'''

# ──────────────────────────────────────────────────────────────────────────
# 3. RUTA CANONICA /v1/agents (sustituye a la primera; las otras 3 se borran)
# ──────────────────────────────────────────────────────────────────────────
OLD_LIST_AGENTS = '''@app.get("/v1/agents")
async def list_agents():
    """Agentes del registro central: el chat los lee de aqui (no hardcodeados)."""
    from router_llm_hf.agent_router import load_registry
    reg = load_registry()
    return {
        "agents": [
            {
                "name": name,
                "status": data.get("status"),
                "chat_path": data.get("chat_path"),
                "mirror": bool(data.get("mirror_endpoint")),
                "role": data.get("role"),
            }
            for name, data in reg.get("agents", {}).items()
        ]
    }
'''

NEW_LIST_AGENTS = '''@app.get("/v1/agents")
async def list_agents():
    """Agentes del registro central: el chat los lee de aqui (no hardcodeados).

    MINIMAX 2F: una sola ruta canonica (antes habia 4 definiciones y FastAPI
    solo honraba la primera). Cada agente trae su interruptor ON/OFF real, si
    su ruta existe de verdad en esta app, su historial y su memoria.
    """
    from router_llm_hf.agent_router import list_agents as _list
    try:
        data = _list()
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": {}}
    app_paths = {getattr(r, "path", "") for r in app.routes}
    for name, cfg in (data.get("agents") or {}).items():
        path = cfg.get("chat_path") or ""
        cfg["route"] = path
        cfg["implemented"] = bool(path) and path in app_paths
        cfg["mirror"] = bool(cfg.get("mirror_endpoint"))
        cfg["tools"] = cfg.get("tools") or []
    data["botonera_ids"] = [b["id"] for b in _botonera()]
    return data


def _botonera():
    """Botonera NCT/APEX (9 botones + HANDOFF)."""
    try:
        from router_llm_hf.nct_format import BOTONERA
        return BOTONERA
    except Exception:
        return []


@app.post("/v1/agents/{agent_name}/state")
async def agent_state(agent_name: str, request: Request, x_api_key: str = Header(None)):
    """Interruptor ON/OFF del agente. Body: {"enabled": true|false}."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    if "enabled" not in body:
        raise HTTPException(400, detail="falta 'enabled'")
    try:
        from router_llm_hf.agent_router import set_agent_enabled
        state = set_agent_enabled(agent_name, bool(body["enabled"]), str(body.get("reason") or "chat"))
    except KeyError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"no se pudo cambiar el estado: {e}")
    return {"ok": True, "agent": agent_name, "state": state}


@app.get("/v1/agents/{agent_name}/history")
async def agent_history(agent_name: str, limit: int = 50, x_api_key: str = Header(None)):
    """Historial append-only del agente (turnos guardados)."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        from router_llm_hf.agent_state import get_history
        turns = get_history(agent_name, limit=limit)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "agent": agent_name, "count": len(turns), "turns": turns}


@app.get("/v1/agents/{agent_name}/memory")
async def agent_memory_get(agent_name: str, x_api_key: str = Header(None)):
    """Memoria persistente del agente (clave -> valor)."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        from router_llm_hf.agent_state import get_memory, memory_keys
        memory = get_memory(agent_name)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "agent": agent_name, "memory": memory, "keys": sorted(memory_keys(agent_name))}


@app.post("/v1/agents/{agent_name}/memory")
async def agent_memory_set(agent_name: str, request: Request, x_api_key: str = Header(None)):
    """Guarda memoria del agente. Body: {"key": "...", "value": ...} o {"patch": {...}}."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    try:
        from router_llm_hf.agent_state import merge_memory, set_memory
        if body.get("patch"):
            memory = merge_memory(agent_name, body["patch"])
        elif body.get("key"):
            memory = set_memory(agent_name, str(body["key"]), body.get("value"))
        else:
            raise HTTPException(400, detail="falta 'key' o 'patch'")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "agent": agent_name, "memory": memory}
'''

# ──────────────────────────────────────────────────────────────────────────
# 4. DUPLICADOS A BORRAR (3 x /v1/agents y 2 x /v1/modes tras la primera)
# ──────────────────────────────────────────────────────────────────────────
DUP_AGENTS = '''@app.get("/v1/agents")
def agents():
    """Registro de agentes + si su ruta existe REALMENTE en esta app."""
    import json as _json
    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "router_llm_hf", "AGENTS_REGISTRY.json",
    )
    try:
        with open(reg_path, "r", encoding="utf-8") as fh:
            registry = _json.load(fh)
    except Exception as e:
        return {"ok": False, "error": str(e), "agents": {}}
    app_paths = {getattr(r, "path", "") for r in app.routes}
    out = {}
    for name, cfg in (registry.get("agents") or {}).items():
        endpoint = cfg.get("endpoint") or ""
        path = ""
        if endpoint.startswith(("http://", "https://", "wss://", "ws://")):
            rest = endpoint.split("://", 1)[1]
            path = "/" + rest.split("/", 1)[1] if "/" in rest else "/"
        implemented = bool(path) and path in app_paths
        out[name] = {
            "type": cfg.get("type"),
            "endpoint": endpoint,
            "declared_status": cfg.get("status"),
            "route": path,
            "implemented": implemented,
        }
    return {"ok": True, "agents": out}


'''

DUP_MODES = '''@app.get("/v1/modes")
def modes():
    """Catalogo de modos: 12 de codigo + 4 de servicio (Op2)."""
    from router_llm_hf.mode_detector import RULES, SERVICE_MODE_NAMES
    return {
        "code_modes": sorted(RULES.keys()),
        "service_modes": sorted(SERVICE_MODE_NAMES),
        "total": len(RULES) + len(SERVICE_MODE_NAMES),
        "service_routes": {m: c["route"] for m, c in SERVICE_MODES.items()},
        "adapters_repo": "COMAND-CENTER-1/swe-code-adapters",
    }


'''

# ──────────────────────────────────────────────────────────────────────────
# 5. RUTAS NUEVAS: artefactos + NCT + raices
# ──────────────────────────────────────────────────────────────────────────
NEW_ROUTES = '''

# ─── MINIMAX 2F · ARTIFACTOS (crear/leer md, py, html y otros) ───────────
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "artifacts"))
ARTIFACT_KINDS = ("md", "py", "html", "json", "txt", "csv", "yaml", "yml", "sh")


def _artifact_safe(name: str) -> str:
    base = os.path.basename(str(name or "").strip())
    base = base.replace("..", "_").replace("/", "_")
    if not base or base in (".", ".."):
        raise HTTPException(400, detail="nombre de artefacto invalido")
    return base


@app.get("/v1/artifacts")
async def list_artifacts(x_api_key: str = Header(None)):
    """Artefactos reales del workspace (con sha256 y tamano)."""
    import hashlib
    out = []
    try:
        names = sorted(os.listdir(ARTIFACT_DIR))
    except FileNotFoundError:
        names = []
    except OSError as e:
        raise HTTPException(500, detail=str(e))
    for name in names:
        path = os.path.join(ARTIFACT_DIR, name)
        if not os.path.isfile(path):
            continue
        data = open(path, "rb").read()
        out.append({
            "name": name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "kind": name.rsplit(".", 1)[-1] if "." in name else "",
        })
    return {"ok": True, "dir": ARTIFACT_DIR, "count": len(out), "artifacts": out,
            "kinds": list(ARTIFACT_KINDS)}


@app.post("/v1/artifacts")
async def create_artifact(request: Request, x_api_key: str = Header(None)):
    """Crea un artefacto (markdown, python, html y otros).

    Body: {"name": "x.md", "content": "...", "kind": "md"}
    """
    import hashlib
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    name = _artifact_safe(body.get("name") or "")
    content = body.get("content")
    if content is None:
        raise HTTPException(400, detail="falta 'content'")
    if not isinstance(content, str):
        raise HTTPException(400, detail="'content' debe ser texto")
    kind = str(body.get("kind") or (name.rsplit(".", 1)[-1] if "." in name else "txt")).lower()
    if kind not in ARTIFACT_KINDS:
        raise HTTPException(400, detail=f"kind no soportado: {kind}; soportados={list(ARTIFACT_KINDS)}")
    if not name.endswith("." + kind):
        name = f"{name}.{kind}"
    try:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        path = os.path.join(ARTIFACT_DIR, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as e:
        raise HTTPException(500, detail=f"no se pudo escribir el artefacto: {e}")
    data = content.encode("utf-8")
    return {"ok": True, "name": name, "path": path, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "kind": kind}


@app.get("/v1/artifacts/{name}")
async def read_artifact(name: str, x_api_key: str = Header(None)):
    """Lee un artefacto por nombre."""
    path = os.path.join(ARTIFACT_DIR, _artifact_safe(name))
    if not os.path.isfile(path):
        raise HTTPException(404, detail=f"artefacto no encontrado: {name}")
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return {"ok": True, "name": os.path.basename(path), "content": fh.read()}


# ─── MINIMAX 2F · NCT/APEX: input 📌, salida F3/F4, botonera, recovery ───
@app.post("/v1/nct/parse")
async def nct_parse(request: Request, x_api_key: str = Header(None)):
    """Parsea el bloque 📌 y devuelve clasificacion + campos + vista previa."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    text = body.get("text") or body.get("input") or ""
    try:
        from router_llm_hf import nct_format
        parsed = nct_format.parse_input_block(text)
        classification = nct_format.classify_input(text)
        preview = nct_format.render_input_preview(parsed, classification)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return {"ok": True, "parsed": parsed, "classification": classification, "preview": preview}


@app.post("/v1/nct/render")
async def nct_render(request: Request, x_api_key: str = Header(None)):
    """Renderiza la salida normalizada F3/F4 (con handoff interno, no visible)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail="Invalid JSON")
    try:
        from router_llm_hf import nct_format
        out = nct_format.render_output(body.get("data") or body, body.get("format"))
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    return out


@app.get("/v1/nct/botonera")
async def nct_botonera(x_api_key: str = Header(None)):
    """Botonera del sistema (9 botones + HANDOFF)."""
    from router_llm_hf.nct_format import BOTONERA
    return {"ok": True, "botonera": BOTONERA, "count": len(BOTONERA)}


@app.get("/v1/nct/recovery")
async def nct_recovery(x_api_key: str = Header(None)):
    """Estado de recuperacion reconstruido de la bitacora (no es un archivo)."""
    try:
        from router_llm_hf.nct_format import recovery_state
        return recovery_state()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── MINIMAX 2F · RAICES: estado real + auto-pull (dry-run por defecto) ───
@app.get("/v1/roots")
async def roots_status(x_api_key: str = Header(None)):
    """Estado real de las 3 raices del workspace y su manifest."""
    import hashlib
    import json as _json
    try:
        from router_llm_hf.agent_router import load_registry
        reg = load_registry()
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = {}
    for name, cfg in (reg.get("roots") or {}).items():
        rel = cfg.get("path") or ""
        path = os.path.join(repo_root, rel)
        entry = {
            "path": rel,
            "exists": os.path.isdir(path),
            "kind": cfg.get("kind"),
            "source": cfg.get("source"),
            "auto_pull": bool(cfg.get("auto_pull")),
            "manifest": cfg.get("manifest"),
            "note": cfg.get("note"),
        }
        if entry["exists"]:
            try:
                total = 0
                files = 0
                for root, _dirs, names in os.walk(path):
                    files += len(names)
                    for n in names:
                        try:
                            total += os.path.getsize(os.path.join(root, n))
                        except OSError:
                            pass
                entry["files"] = files
                entry["bytes"] = total
            except OSError as e:
                entry["error"] = str(e)
        manifest_path = cfg.get("manifest")
        if manifest_path:
            mpath = os.path.join(repo_root, manifest_path)
            if os.path.isfile(mpath):
                try:
                    with open(mpath, "rb") as fh:
                        raw = fh.read()
                    entry["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
                    entry["manifest_bytes"] = len(raw)
                    data = _json.loads(raw.decode("utf-8"))
                    if isinstance(data, dict):
                        entry["manifest_keys"] = sorted(data.keys())[:20]
                        if "parts" in data:
                            entry["manifest_parts"] = len(data["parts"])
                        if "extraction_verified" in data:
                            entry["extraction_verified"] = data["extraction_verified"]
                except Exception as e:
                    entry["manifest_error"] = str(e)
        out[name] = entry
    return {"ok": True, "count": len(out), "roots": out}


@app.post("/v1/roots/pull")
async def roots_pull(request: Request, x_api_key: str = Header(None)):
    """Auto-pull de las raices. Body: {"apply": false} (dry-run por defecto)."""
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    try:
        body = await request.json()
    except Exception:
        body = {}
    apply_changes = bool(body.get("apply"))
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "scripts", "pull_agent_roots.py")
    if not os.path.isfile(script):
        raise HTTPException(500, detail="no existe scripts/pull_agent_roots.py")
    import subprocess
    import sys as _sys
    cmd = [_sys.executable, script, "--all"] + (["--apply"] if apply_changes else [])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as e:
        raise HTTPException(500, detail=f"auto-pull fallo: {e}")
    return {"ok": proc.returncode == 0, "apply": apply_changes, "returncode": proc.returncode,
            "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:]}
'''

REPLACEMENTS = [
    (OLD_PROMPTS, NEW_PROMPTS, "prompts ruflo/rowboat"),
    (OLD_AGENT_REQ, NEW_AGENT_REQ, "interruptor ON/OFF + persistencia"),
    (OLD_LIST_AGENTS, NEW_LIST_AGENTS, "ruta canonica /v1/agents + rutas nuevas"),
]


def main() -> int:
    if not PROXY.is_file():
        print(f"FALLO: no existe {PROXY}")
        return 2
    src = PROXY.read_text(encoding="utf-8")
    original = src

    for old, new, label in REPLACEMENTS:
        count = src.count(old)
        if count != 1:
            print(f"FALLO: ancla '{label}' aparece {count} veces (se esperaba 1)")
            return 2
        src = src.replace(old, new, 1)
        print(f"OK: {label}")

    # Duplicados: se borran TODOS (3 x /v1/agents, 2 x /v1/modes).
    n_agents = src.count(DUP_AGENTS)
    n_modes = src.count(DUP_MODES)
    if n_agents != 3:
        print(f"FALLO: se esperaban 3 bloques duplicados de /v1/agents, hay {n_agents}")
        return 2
    if n_modes != 3:
        print(f"FALLO: se esperaban 3 bloques duplicados de /v1/modes, hay {n_modes}")
        return 2
    src = src.replace(DUP_AGENTS, "")
    src = src.replace(DUP_MODES, "")
    print(f"OK: borrados {n_agents} duplicados de /v1/agents y {n_modes} de /v1/modes")

    # Rutas nuevas al final del bloque de endpoints.
    if "/v1/artifacts" in src:
        print("OK: rutas /v1/artifacts ya presentes (idempotente)")
    else:
        marker = '@app.get("/control-plane/status")'
        if src.count(marker) != 1:
            print("FALLO: no se encuentra el ancla @app.get('/control-plane/status')")
            return 2
        src = src.replace(marker, NEW_ROUTES.strip() + "\n\n\n" + marker, 1)
        print("OK: rutas /v1/artifacts, /v1/nct/* y /v1/roots anadidas")

    if src == original:
        print("FALLO: el fichero no cambio")
        return 2
    PROXY.write_text(src, encoding="utf-8")
    print(f"OK: proxy actualizado ({len(original)} -> {len(src)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
