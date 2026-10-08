"""PUNTO 6: mini-orquestador por chat (MVP), con interruptor ON/OFF guardado en el servidor. OFF por defecto.

Reutiliza, sin sistema paralelo:
  * el agente `orquestador-g0` (tabla agents / /chat/agents) como planificador y como quien resume;
  * el DSL DAG riu.dag/v1 (`dag.validate`, `dag.topo_order`, `dag.EXECUTOR_CONTRACT`) para el plan;
  * el patron de agent-microkernel/kernel/runner.py: niveles del DAG en paralelo, INPUT_BLOCK literal, estado por nodo;
  * los chats hijos del PUNTO 5 (`memoria_loader.create_child`): cada nodo corre en su propio hijo con el INPUT_BLOCK
    del padre literal y memoria propia; el turno del hijo pasa por el camino normal de puente_chat (`_chat`).
Limites duros: <= 3 nodos, timeout por nodo, sin recursion (un hijo nunca orquesta), solo fichas API (nunca enciende
un Job L4) y sin herramientas en los nodos (ninguna puede crear Jobs). Todo dentro del proceso del Router.
Con el interruptor en OFF puente_chat no cambia en nada: `activo()` devuelve False y el chat sigue su camino de siempre.
"""
from __future__ import annotations

import concurrent.futures as cf
import contextvars
import json
import os
import re
import threading
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import memoria_loader as ml

MAX_NODOS = 3
NODE_TIMEOUT_S = int(os.getenv("RIU_ORQ_NODE_TIMEOUT_S") or "150")
NODE_MAX_TOKENS = 1200
PLAN_INTENTOS = 2  # el planificador se reintenta una vez antes del plan de respaldo
PLAN_BACKOFF_S = float(os.getenv("RIU_ORQ_PLAN_BACKOFF_S") or "2")
PLANNER = "orquestador-g0"
TOGGLE_KEY = "orquestador"
RUN_PREFIX = "orq:run:"
EN_RUN: contextvars.ContextVar[bool] = contextvars.ContextVar("riu_orq_en_run", default=False)
_RUN_ID = re.compile(r"^orq-[0-9]{13}-[0-9a-f]{4}$")
_LOCK = threading.Lock()


def es_hija(sesion: str) -> bool:
    return ":ag:" in str(sesion)


def estado(sesion: str) -> dict[str, Any]:
    rec = ml._one(ml._file_scope(sesion), TOGGLE_KEY) or {}
    return {"sesion": sesion, "activo": bool(rec.get("activo")), "ts": rec.get("ts"),
            "limites": {"max_nodos": MAX_NODOS, "timeout_nodo_s": NODE_TIMEOUT_S, "herramientas_en_nodos": False,
                        "recursion": False, "solo_fichas_api": True}}


def poner(sesion: str, activo_: bool) -> dict[str, Any]:
    if es_hija(sesion):
        raise ml.ChildError("ORQUESTADOR_EN_HIJA", 422)
    ml._memory().save(ml._file_scope(sesion), TOGGLE_KEY, {"activo": bool(activo_), "ts": time.time()})
    return estado(sesion)


def activo(sesion: str) -> bool:
    """Lo unico que puente_chat pregunta. Ante cualquier duda: False (= chat de siempre)."""
    try:
        if EN_RUN.get() or es_hija(sesion):
            return False
        return bool((ml._one(ml._file_scope(sesion), TOGGLE_KEY) or {}).get("activo"))
    except Exception:  # noqa: BLE001
        return False


# --- runs: registros 'orq:run:<id>' en la memoria del padre (la ultima version manda) ---
def _save_run(run: dict[str, Any]) -> None:
    ml._memory().sqlite.save(ml._file_scope(run["sesion"]), RUN_PREFIX + run["run_id"], run)  # solo SQLite: sin nodo de grafo por version


def leer_run(sesion: str, run_id: str) -> dict[str, Any]:
    if not _RUN_ID.match(run_id):
        raise ml.ChildError("RUN_INVALIDO", 422)
    run = ml._one(ml._file_scope(sesion), RUN_PREFIX + run_id)
    if not run:
        raise ml.ChildError("RUN_NO_EXISTE", 404)
    return run


def listar_runs(sesion: str) -> dict[str, Any]:
    rows = ml._q("SELECT key,data FROM memoria_yaiwes WHERE scope=? AND substr(key,1,8)='orq:run:' ORDER BY id DESC",
                 (ml._file_scope(sesion),))
    runs, seen = [], set()
    for r in rows:
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        d = json.loads(r["data"])
        runs.append({"run_id": d.get("run_id"), "estado": d.get("estado"), "nodos": len(d.get("nodos") or []),
                     "ts_inicio": d.get("ts_inicio"), "ts_fin": d.get("ts_fin")})
    return {"sesion": sesion, "runs": runs}


# --- plan ---
def _json_obj(text: str) -> Any:
    body = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(text or "").strip())
    m = re.search(r"\{.*\}", body, re.S)
    return json.loads(m.group(0)) if m else None


def normalizar_plan(raw: Any, agentes: set[str], max_n: int = MAX_NODOS) -> list[dict[str, Any]]:
    """<= max_n nodos n1..nN, agente conocido (si no, orquestador-g0), needs solo hacia nodos anteriores (sin ciclos)."""
    items = (raw or {}).get("nodos") if isinstance(raw, dict) else raw
    nodos: list[dict[str, Any]] = []
    ids_map: dict[str, str] = {}
    for it in (items if isinstance(items, list) else [])[:max(1, min(MAX_NODOS, int(max_n)))]:
        if not isinstance(it, dict):
            continue
        ins = str(it.get("instrucciones") or it.get("instructions") or "").strip()
        if not ins:
            continue
        nid = "n%d" % (len(nodos) + 1)
        ids_map[str(it.get("id") or nid)] = nid
        ag = str(it.get("agente") or it.get("agent") or "")
        needs = [ids_map[str(d)] for d in (it.get("needs") or []) if str(d) in ids_map and ids_map[str(d)] != nid]
        nodos.append({"id": nid, "agente": ag if ag in agentes else PLANNER, "instrucciones": ins[:4000], "needs": needs})
    return nodos


class PlanError(RuntimeError):
    pass


_SECRETO = re.compile(r"(gsk_|nvapi-|hf_|sk-|ghp_|github_pat_|Bearer\s+)[A-Za-z0-9_\-.]{6,}", re.I)


def motivo(exc: BaseException) -> str:
    """Solo la razon (codigo/tipo), nunca cuerpos completos; cualquier cosa con forma de clave se tapa."""
    return _SECRETO.sub("[REDACTADO]", str(exc) or type(exc).__name__)[:200]


def _razon_api(s: int, d: Any) -> str:
    err = d.get("error") if isinstance(d, dict) else None
    if isinstance(err, dict):
        err = err.get("code") or err.get("type") or "error"
    if isinstance(d, dict) and not err and not d.get("choices"):
        err = "SIN_CHOICES"
    return "HTTP %s%s" % (s, (": " + str(err)[:80]) if err else "")


def _llm(model: str, msgs: list[dict[str, str]], max_tokens: int) -> str:
    from plugins.puente_chat import plugin as P
    _, proveedor, modelo, tope = P.FICHAS[model]
    s, d = P._llamar_api(proveedor, modelo, msgs, max_tokens, tope, None)
    if s >= 400 or s == 0 or not isinstance(d, dict) or not d.get("choices"):
        raise PlanError("PLANIFICADOR_NO_RESPONDE " + _razon_api(s, d))
    return str((d["choices"][0].get("message") or {}).get("content") or "")


RESPALDO = [{"id": "n1", "agente": PLANNER, "instrucciones": "Resuelve el INPUT_BLOCK.", "needs": []}]


def planificar(model: str, input_block: str, max_n: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Plan del modelo (hasta PLAN_INTENTOS intentos, con espera corta) o el plan de respaldo de 1 nodo.
    Devuelve (nodos, info) con info = {"plan_origen": "modelo"|"respaldo", "plan_intentos": n, "plan_error": razon|None}."""
    st = ml.get_store()
    agentes = {a["id"]: a for a in st.agents()}
    g0 = agentes.get(PLANNER) or {}
    lista = "\n".join("- %s: %s" % (a["id"], a.get("role") or "") for a in agentes.values())
    sistema = (str(g0.get("system_prompt") or "Eres el orquestador.") + " " + ml_contract()
               + "\nDevuelve SOLO JSON: {\"nodos\":[{\"id\":\"n1\",\"agente\":\"<id>\",\"instrucciones\":\"...\",\"needs\":[]}]}"
               + " con como maximo %d nodos (usa exactamente %d si la tarea lo permite). Agentes disponibles:\n%s" % (max_n, max_n, lista))
    error = None
    for intento in range(1, PLAN_INTENTOS + 1):
        if intento > 1:
            time.sleep(PLAN_BACKOFF_S)
        try:
            text = _llm(model, [{"role": "system", "content": sistema},
                                {"role": "user", "content": "INPUT_BLOCK (literal):\n" + input_block}], 700)
            try:
                raw = _json_obj(text)
            except ValueError:
                raise PlanError("PLAN_JSON_INVALIDO") from None
            if raw is None:
                raise PlanError("PLAN_SIN_JSON")
            nodos = normalizar_plan(raw, set(agentes), max_n)
            if not nodos:
                raise PlanError("PLAN_SIN_NODOS_VALIDOS")
            return nodos, {"plan_origen": "modelo", "plan_intentos": intento, "plan_error": None}
        except Exception as exc:  # noqa: BLE001 - se guarda la razon y se reintenta / cae al respaldo
            error = motivo(exc) if isinstance(exc, PlanError) else "%s: %s" % (type(exc).__name__, motivo(exc))
    return [dict(n) for n in RESPALDO], {"plan_origen": "respaldo", "plan_intentos": PLAN_INTENTOS, "plan_error": error}


def ml_contract() -> str:
    from . import dag as dagmod
    return dagmod.EXECUTOR_CONTRACT


def dag_de(nodos: list[dict[str, Any]], model: str, run_id: str) -> dict[str, Any]:
    from plugins.puente_chat import plugin as P
    _, proveedor, modelo, _ = P.FICHAS[model]
    return {"schema": "riu.dag/v1", "id": run_id,
            "nodes": [{"id": n["id"], "agent": n["agente"], "model": {"provider": proveedor, "model": modelo},
                       "instructions": n["instrucciones"], "needs": n["needs"], "max_tokens": NODE_MAX_TOKENS} for n in nodos]}


# --- ejecucion ---
def _turno_hijo(model: str, hija: str, nodo: dict[str, Any], deps: dict[str, str]) -> dict[str, Any]:
    from plugins.puente_chat import plugin as P
    EN_RUN.set(True)  # este hilo es un nodo: nunca orquesta (sin recursion)
    P._SIN_HERRAMIENTAS.set(True)  # sin herramientas: ningun nodo puede crear Jobs
    user = "NODO %s (agente %s)\nINSTRUCCIONES:\n%s" % (nodo["id"], nodo["agente"], nodo["instrucciones"])
    if deps:
        user += "\n\nSALIDAS DE NODOS PREVIOS:\n" + "\n".join("[%s]\n%s" % (k, v[:3000]) for k, v in deps.items())
    return P._chat({"model": model, "sesion": hija, "max_tokens": NODE_MAX_TOKENS, "messages": [{"role": "user", "content": user}]})


def _nodo_directo(model: str, input_block: str, nodo: dict[str, Any]) -> dict[str, Any]:
    """Nodo del plan de respaldo: misma ficha (orquestador-g0), contrato e INPUT_BLOCK literal, sin hijo, sin herramientas,
    sin escribir memoria (el turno del padre lo guarda ejecutar con la respuesta)."""
    EN_RUN.set(True)
    g0 = ml.get_store().agent(nodo["agente"]) or {}
    sistema = (str(g0.get("system_prompt") or "") + " " + ml_contract()).strip()
    user = "INPUT_BLOCK (literal):\n%s\n\nNODO %s (agente %s, plan de respaldo)\nINSTRUCCIONES:\n%s" % (
        input_block, nodo["id"], nodo["agente"], nodo["instrucciones"])
    txt = _llm(model, [{"role": "system", "content": sistema}, {"role": "user", "content": user}], NODE_MAX_TOKENS)
    return {"model": model, "choices": [{"message": {"role": "assistant", "content": txt}}]}


def ejecutar(p: dict[str, Any]) -> dict[str, Any]:
    tok = EN_RUN.set(True)  # se restaura al salir: los hilos del pool de chat_async se reutilizan
    try:
        return _ejecutar(p)
    except Exception as exc:  # noqa: BLE001 - el orquestador nunca tumba el chat
        return {"error": "ORQUESTADOR_FALLO", "detalle": "%s: %s" % (type(exc).__name__, str(exc)[:200])}
    finally:
        EN_RUN.reset(tok)


def _ejecutar(p: dict[str, Any]) -> dict[str, Any]:
    """Turno del padre con el orquestador ON: plan (<=3 nodos) -> un hijo por nodo -> resumen en el padre."""
    from plugins.puente_chat import plugin as P
    from . import dag as dagmod
    model = str(p.get("model") or "")
    sesion = str(p.get("sesion") or "general")[:60]
    mensajes = list(p.get("messages") or [])
    input_block = next((str(m.get("content", "")) for m in reversed(mensajes) if m.get("role") == "user"), "")
    if model not in P.FICHAS or model in P.ESPECIALES:
        return {"error": "ORQUESTADOR_SOLO_FICHAS_API", "detalle": "elige un modelo API (p.ej. groq-qwen-3-8)"}
    if not input_block.strip():
        return {"error": "ORQUESTADOR_SIN_INPUT"}
    t0 = time.time()
    run_id = "orq-%d-%s" % (int(t0 * 1000), os.urandom(2).hex())
    max_n = max(1, min(MAX_NODOS, int(p.get("orquestador_nodos") or MAX_NODOS)))
    run: dict[str, Any] = {"run_id": run_id, "sesion": sesion, "estado": "PLANIFICANDO", "modelo": model,
                           "input_block_sha256": ml._sha256(input_block), "ts_inicio": t0, "ts_fin": None, "nodos": [], "resumen": None}
    _save_run(run)
    nodos, info = planificar(model, input_block, max_n)
    run.update(info)  # plan_origen, plan_intentos, plan_error (solo la razon): campos extra del detalle del run
    respaldo = info["plan_origen"] == "respaldo"
    dag = dag_de(nodos, model, run_id)
    errs = dagmod.validate({**dag, "input_block": input_block})
    if errs:  # no deberia pasar (plan normalizado); fail-closed
        run.update(estado="FALLO", ts_fin=time.time(), error="DAG_INVALIDO: " + "; ".join(errs)[:300])
        _save_run(run)
        return {"error": "ORQUESTADOR_DAG_INVALIDO", "run_id": run_id}
    run["dag"] = dag
    for n in nodos:
        # plan de respaldo: el nodo corre dentro del turno del padre, sin abrir un chat hijo (no deja hijos 'orquestador-g0' sueltos)
        hija = None if respaldo else ml.create_child(sesion, input_block, dag, agente=n["agente"])["sesion_hija"]
        run["nodos"].append({"id": n["id"], "agente": n["agente"], "instrucciones": n["instrucciones"], "needs": n["needs"],
                             "sesion_hija": hija, "estado": "PENDIENTE", "respuesta": None, "error": None, "ms": None})
    run["estado"] = "EJECUTANDO"
    _save_run(run)
    by_id = {x["id"]: x for x in run["nodos"]}
    salidas: dict[str, str] = {}
    pool = cf.ThreadPoolExecutor(max_workers=MAX_NODOS, thread_name_prefix="riu-orq")
    try:
        pendientes = list(nodos)  # needs solo apunta a nodos anteriores (normalizar_plan): siempre hay un nivel listo
        while pendientes:
            nivel = [n for n in pendientes if all(by_id[d]["estado"] not in ("PENDIENTE", "EJECUTANDO") for d in n["needs"])]
            if not nivel:
                for n in pendientes:
                    by_id[n["id"]].update(estado="BLOQUEADO", error="dependencias en ciclo")
                break
            pendientes = [n for n in pendientes if n not in nivel]
            futs = {}
            for n in nivel:
                rec = by_id[n["id"]]
                malos = [d for d in n["needs"] if by_id[d]["estado"] != "HECHO"]
                if malos:
                    rec.update(estado="BLOQUEADO", error="dependencia sin terminar: " + ",".join(malos))
                    continue
                rec["estado"] = "EJECUTANDO"
                rec["_t"] = time.time()
                deps = {d: salidas[d] for d in n["needs"]}
                if respaldo:
                    futs[n["id"]] = pool.submit(contextvars.Context().run, _nodo_directo, model, input_block, n)
                else:
                    futs[n["id"]] = pool.submit(contextvars.Context().run, _turno_hijo, model, rec["sesion_hija"], n, deps)
            _save_run(_publico(run))
            for nid, fut in futs.items():
                rec = by_id[nid]
                restante = max(1.0, NODE_TIMEOUT_S - (time.time() - rec["_t"]))
                try:
                    out = fut.result(timeout=restante)
                except cf.TimeoutError:
                    rec.update(estado="TIMEOUT", error="sin respuesta en %ds" % NODE_TIMEOUT_S)
                except Exception as exc:  # noqa: BLE001
                    rec.update(estado="FALLO", error="%s: %s" % (type(exc).__name__, str(exc)[:200]))
                else:
                    if isinstance(out, dict) and out.get("choices"):
                        txt = str((out["choices"][0].get("message") or {}).get("content") or "")
                        rec.update(estado="HECHO", respuesta=txt[:6000], modelo=out.get("model"))
                        salidas[nid] = txt
                    else:
                        rec.update(estado="FALLO", error=str((out or {}).get("error") or out)[:300])
                rec["ms"] = int((time.time() - rec.pop("_t")) * 1000)
            _save_run(_publico(run))
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    unico = run["nodos"][0] if respaldo and run["nodos"] else None
    resumen = unico["respuesta"] if unico and unico["estado"] == "HECHO" and unico["respuesta"] else resumir(model, input_block, run["nodos"])
    run.update(estado="HECHO" if all(x["estado"] == "HECHO" for x in run["nodos"]) else "PARCIAL", resumen=resumen, ts_fin=time.time())
    _save_run(_publico(run))
    guardada = P._guardar(sesion, model, input_block, resumen)  # el resumen queda como turno del padre (/chat/history)
    resumen_corto = [{k: x.get(k) for k in ("id", "agente", "sesion_hija", "estado", "ms")} for x in run["nodos"]]
    return {"model": model, "choices": [{"index": 0, "message": {"role": "assistant", "content": resumen}, "finish_reason": "stop"}],
            "usage": None, "herramientas": [], "memoria_guardada": guardada,
            "orquestador": {"run_id": run_id, "estado": run["estado"], "nodos": resumen_corto}}


def _publico(run: dict[str, Any]) -> dict[str, Any]:
    return {**run, "nodos": [{k: v for k, v in x.items() if not k.startswith("_")} for x in run["nodos"]]}


def resumir(model: str, input_block: str, nodos: list[dict[str, Any]]) -> str:
    bloques = "\n\n".join("[%s · %s · %s]\n%s" % (n["id"], n["agente"], n["estado"], n.get("respuesta") or n.get("error") or "")
                          for n in nodos)
    g0 = ml.get_store().agent(PLANNER) or {}
    try:
        txt = _llm(model, [{"role": "system", "content": str(g0.get("system_prompt") or "") + " Resume para el usuario, en espanol y "
                            "breve, el resultado de los nodos; no inventes nada que no este en sus salidas; marca los GAP."},
                           {"role": "user", "content": "INPUT_BLOCK (literal):\n" + input_block + "\n\nSALIDAS DE LOS NODOS:\n" + bloques}], 900)
        if txt.strip():
            return txt
    except Exception:  # noqa: BLE001
        pass
    return "Resultados del orquestador:\n\n" + bloques


# --- rutas (misma auth que /chat/history) ---
class Toggle(BaseModel):
    activo: bool


def build_router() -> APIRouter:
    r = APIRouter()

    def _ok(fn: Any, *a: Any) -> Any:
        try:
            return fn(*a)
        except ml.ChildError as exc:
            raise HTTPException(status_code=exc.status, detail=exc.code) from exc

    def _check(sesion: str) -> None:
        if not ml._SESION.match(sesion):
            raise HTTPException(status_code=422, detail="SESION_INVALIDA")

    @r.get("/chat/orquestador/{sesion}")
    def get_toggle(sesion: str, _owner: str = Depends(ml._auth)) -> dict[str, Any]:
        _check(sesion)
        return estado(sesion)

    @r.post("/chat/orquestador/{sesion}")
    def set_toggle(sesion: str, req: Toggle, _owner: str = Depends(ml._auth)) -> dict[str, Any]:
        _check(sesion)
        return _ok(poner, sesion, req.activo)

    @r.get("/chat/orquestador/{sesion}/runs")
    def runs(sesion: str, _owner: str = Depends(ml._auth)) -> dict[str, Any]:
        _check(sesion)
        return listar_runs(sesion)

    @r.get("/chat/orquestador/{sesion}/runs/{run_id}")
    def run(sesion: str, run_id: str, _owner: str = Depends(ml._auth)) -> dict[str, Any]:
        _check(sesion)
        return _ok(leer_run, sesion, run_id)

    return r
