"""Server-only binding to existing chat/Harness, HF persistence and CIT-50."""
from __future__ import annotations
import base64
import hashlib
import json
import time
from pathlib import Path
from .trigger_contract import ContractError, canonical, sha256, _safe_path
from .trigger_engine import HostPorts

def build_ports(host: dict) -> HostPorts:
    from mvp import hf_store
    from plugins.puente_chat import plugin as puente
    if not isinstance(host, dict) or not host.get("authenticated") or not host.get("trusted_host"):
        raise ContractError("HOST_AUTH_REQUIRED")
    control, banco, store, watch = (host.get(k) for k in ("control", "banco", "queue_store", "watch_store"))
    root = host.get("root")
    if not banco or not control or not store or not isinstance(root, Path) or not root.is_dir():
        raise ContractError("BLOCKED_PORT_NOT_CONNECTED")
    root = root.resolve()
    project, loop, sesion = host["project_id"], host.get("loop_id"), host.get("sesion", "web-general")

    def key_name(key):
        return "yaiwes/dsl/" + hashlib.sha256(key.encode("utf8")).hexdigest() + ".json"

    def hf_token():
        return control.credencial("hf", banco, estricto=False)

    def load(key):
        try:
            return json.loads(hf_store.leer(hf_token(), key_name(key))["valor"])
        except hf_store.NoExiste:
            return None

    def save(key, document):
        raw = canonical(document).decode("utf8")
        if key.startswith("dsl-config:") and hasattr(store, "db"):
            with store.db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                old = load(key)
                if document.get("revision") != int((old or {}).get("revision", 0)) + 1:
                    conn.execute("ROLLBACK")
                    raise ContractError("REVISION_CONFLICT")
                hf_store.guardar(hf_token(), key_name(key), raw)
                read = hf_store.leer(hf_token(), key_name(key))["valor"]
                if sha256(read.encode("utf8")) != sha256(raw.encode("utf8")):
                    conn.execute("ROLLBACK")
                    return False
                conn.execute("COMMIT")
                return True
        hf_store.guardar(hf_token(), key_name(key), raw)
        read = hf_store.leer(hf_token(), key_name(key))["valor"]
        return sha256(read.encode("utf8")) == sha256(raw.encode("utf8"))

    def anchor(ref):
        if not isinstance(ref, str) or not ref.startswith("ancla:"):
            raise ContractError("BAD_ANCHOR")
        name = ref.split(":", 1)[1]
        if not name or name.startswith(".") or ".." in name or "/" in name or "\\" in name:
            raise ContractError("BAD_ANCHOR")
        row = control.d.get("proyectos", {}).get(project) or {}
        allowed = row.get("anclas") or []
        if not isinstance(allowed, list) or not any(label in allowed for label in
                (ref, name, "archivo:" + name, "constitucion:" + name)):
            raise ContractError("ANCHOR_OUT_OF_SCOPE")
        path = control.ruta_de(name, sesion)
        if not path:
            raise ContractError("FUENTE_ANCLADA_NO_LEIBLE")
        raw = hf_store.leer(hf_token(), path)["valor"]
        data = base64.b64decode(raw, validate=True)
        if len(data) > 512_000:
            raise ContractError("ANCHOR_TOO_LARGE")
        digest = sha256(data)
        return {"bytes": data, "sha256": digest, "evidence_ref": "hf:" + path + ":" + digest}

    def constitution():
        path = root / "plugins" / "puente_chat" / "constitucion" / "CONSTITUCION-YAIWES.json"
        raw = path.read_bytes()
        row = control.d.get("proyectos", {}).get(project) or {}
        overlays = [anchor("ancla:" + str(label).partition(":")[2])["bytes"]
                    for label in row.get("anclas", []) if str(label).startswith("constitucion:")]
        return {"bytes": raw, "overlay_bytes": overlays, "anchor_set_checked": True}

    def facts(pid, lid):
        row = control.d.get("proyectos", {}).get(pid)
        if not isinstance(row, dict):
            raise ContractError("PROJECT_NOT_FOUND")
        return {"backend_required": True, "frontend_required": False, "approved_scope": False,
                "source_exists": {}}

    def queue_create(pid, lid, contracts, duration_minutes=60):
        tasks = [{"id": c["id"], "title": c["name"][:150], "type": "handoff",
                  "prompt": "DSL:" + sha256(canonical(c)), "depends_on": list(c.get("depends_on", []))}
                 for c in contracts]
        q = store.create({"title": "LOOP " + lid, "chat_id": pid,
                          "tasks": tasks, "mode": "dsl", "max_model_calls": 100})
        try:
            q = store.start(q["queue_id"], seconds=duration_minutes * 60)
            for c in contracts:
                if not c["enabled"]:
                    store.disable_dsl_task(q["queue_id"], c["id"])
            wid = None
            if watch is not None:
                result = watch.create({"name": "YAIWES " + lid, "target_type": "queue",
                        "target_id": q["queue_id"], "duration_minutes": duration_minutes,
                        "interval_seconds": 30})
                wid = result["id"]
        except Exception as e:
            try:
                if store.get(q["queue_id"])["status"] == "running":
                    store.control(q["queue_id"], "cancel")
            except Exception:
                raise ContractError("QUEUE_ORPHAN_RECONCILIATION_REQUIRED") from None
            raise ContractError("QUEUE_START_FAILED") from e
        return {"queue_id": q["queue_id"], "watchdog_id": wid}

    def queue_claim(req):
        state = load("dsl-config:" + req["project_id"] + ":" + req["loop_id"])
        if not isinstance(state, dict) or not state.get("queue_id"):
            raise ContractError("QUEUE_NOT_CONNECTED")
        c = next((c for c in state.get("contracts", []) if c["id"] == req["trigger_id"]), None)
        if not c or sha256(canonical(c)) != req["contract_sha256"]:
            raise ContractError("CONTRACT_CHANGED_DURING_TASK")
        claim = store.claim_dsl_for(state["queue_id"], req["trigger_id"])
        if not claim.get("claimed"):
            raise ContractError(claim.get("error", "QUEUE_NOT_CLAIMED"))
        return {"claimed": True, "receipt_ref": "cit:" + claim["queue_id"] + ":" + claim["task_id"]}

    def queue_complete(ref, receipt):
        try:
            _, qid, tid = ref.split(":", 2)
        except ValueError:
            raise ContractError("QUEUE_RECEIPT_INVALID")
        if not store.complete(qid, tid, receipt, ok=receipt.get("verification") == "PASS"):
            raise ContractError("QUEUE_COMPLETION_FAILED")
        row = store.get(qid)
        task = next((t for t in row["tasks"] if t["id"] == tid), None)
        expected = "succeeded" if receipt.get("verification") == "PASS" else "failed"
        if not task or task.get("status") != expected or not task.get("receipt_id"):
            raise ContractError("QUEUE_COMPLETION_STATE_MISMATCH")
        return {"ok": True, "evidence_ref": "cit:" + qid + ":" + task["receipt_id"]}

    def roles_resolve(roles):
        found = {}
        for role, item in roles.items():
            model_id, agent_id = item["model_id"], item["agent_id"]
            known = model_id in puente.FICHAS or model_id in puente.RESPALDO
            agent = control.d.get("agentes", {}).get(agent_id)
            ready = bool(known and agent and control.d.get("agentes_on")
                         and agent.get("recurso") == model_id)
            found[role] = {"model_id": model_id, "agent_id": agent_id,
                           "available": ready,
                           "reason": "READY" if ready else "MODEL_OR_AGENT_UNAVAILABLE"}
        return found

    def model(selection, prompt):
        agent = control.d.get("agentes", {}).get(selection.get("agent_id"))
        if not agent or not control.d.get("agentes_on") or agent.get("recurso") != selection.get("model_id"):
            raise ContractError("ROLE_PAIR_UNAVAILABLE")
        messages = [{"role": "system", "content":
          "Follow the attached INPUT BLOCK verbatim. Return one JSON object with status,"
          " data and evidence_refs. status must be READY, NEED_INPUT or BLOCKED."
          " No native tool calls; the backend executes approved tools separately."}]
        if isinstance(agent.get("sistema"), str) and agent.get("sistema"):
            messages.append({"role": "system", "content": agent["sistema"]})
        messages.append({"role": "user", "content": json.dumps(prompt, ensure_ascii=False)})
        response = puente._chat({"model": selection["model_id"], "messages": messages,
             "sesion": sesion, "max_tokens": 4096, "tools_habilitadas": False,
             "motor": False, "cap_tools": "none", "rondas_tools_max": 0})
        if not isinstance(response, dict) or response.get("error"):
            raise ContractError("MODEL_PROVIDER_FAILURE")
        choice = (response.get("choices") or [{}])[0]
        if choice.get("message", {}).get("tool_calls") or response.get("tool_calls"):
            raise ContractError("MODEL_TOOLCALLS_DISABLED")
        finish = response.get("finish_reason") or choice.get("finish_reason")
        content = response.get("reply") or choice.get("message", {}).get("content")
        try:
            parsed = json.loads(content) if isinstance(content, str) else None
        except json.JSONDecodeError:
            parsed = None
        if finish != "stop" or not isinstance(parsed, dict):
            raise ContractError("PARTIAL_MODEL_OUTPUT")
        return {"finish_reason": finish, "status": parsed.get("status"),
                "data": parsed.get("data"), "evidence_refs": parsed.get("evidence_refs", [])}

    def safe_target(path):
        _safe_path(path)
        if any(q.startswith(".") or q.lower() in {"secret", "secrets", "keys", "credentials", "tokens"}
               for q in path.split("/")) or path.lower().endswith((".env", ".key", ".pem", ".p12")):
            raise ContractError("SENSITIVE_PATH_DENIED")
        target = (root / path).resolve()
        if not target.is_relative_to(root):
            raise ContractError("PATH_OUT_OF_SCOPE")
        return target

    def tool(op, args, context):
        from .trigger_contract import WRITE_OPS
        if op in WRITE_OPS:
            raise ContractError("AUTHORIZED_GITHUB_WRITER_NOT_CONNECTED")
        if not isinstance(args, dict):
            raise ContractError("BAD_TOOL_ARGS")
        target = safe_target(args["path"]) if "path" in args else root
        if op == "inspect_workspace":
            names = sorted(p.name for p in root.iterdir())[:100]
            return {"ok": True, "entries": names,
                    "evidence_ref": "fs:" + sha256(canonical(names))}
        if op == "finish":
            return {"ok": True, "evidence_ref": "dsl:finish"}
        if op not in ("read_text", "verify_exists", "verify_contains"):
            raise ContractError("TOOL_NOT_AVAILABLE")
        if op == "verify_exists":
            ok = target.is_file()
            return {"ok": ok, "evidence_ref": "fs:" + sha256(str(target).encode())}
        if not target.is_file() or target.stat().st_size > 1_000_000:
            raise ContractError("FILE_NOT_READABLE")
        raw = target.read_bytes()
        try:
            value = raw.decode("utf8")
        except UnicodeDecodeError:
            raise ContractError("FILE_NOT_UTF8")
        if op == "verify_contains":
            ok = isinstance(args.get("text"), str) and args["text"] in value
            return {"ok": ok, "evidence_ref": "fs:" + sha256(raw)}
        return {"ok": True, "text": value, "evidence_ref": "fs:" + sha256(raw)}

    def approve(req):
        row = load(f"dsl-approval:{req['project_id']}:{req['loop_id']}:{req['trigger_id']}")
        if not isinstance(row, dict):
            return {"approved": False}
        if (row.get("writer") != "N4" or row.get("approved") is not True
                or row.get("contract_sha256") != req["contract_sha256"]
                or row.get("constitution_sha256") != req["constitution_sha256"]
                or row.get("write_paths") != req["write_paths"]
                or time.time() - row.get("timestamp", 0) > 1800):
            return {"approved": False}
        return row

    return HostPorts(load, save, constitution, anchor, facts, queue_claim,
                     model, tool, approve, queue_complete,
                     queue_create, store.control, store.get, store.events, roles_resolve,
                     False)
