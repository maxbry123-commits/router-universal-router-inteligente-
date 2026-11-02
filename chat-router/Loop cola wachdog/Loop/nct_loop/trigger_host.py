"""Server-only binding to existing chat/Harness, HF persistence and CIT-50."""
from __future__ import annotations
import base64
import hashlib
import json
import time
import tempfile
import re
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
    project_row = control.d.get("proyectos", {}).get(project) or {}
    github_ready = (project_row.get("repo") ==
        "maxbry123-commits/router-universal-router-inteligente-" and
        project_row.get("branch") == "main" and
        isinstance(project_row.get("write_paths"), list) and
        bool(project_row["write_paths"]) and
        host.get("write_paths") == project_row["write_paths"])

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
        if key.startswith(("dsl-config:","dsl-gaps:")) and hasattr(store, "db"):
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

    def github_head():
        if not github_ready:
            raise ContractError("PROJECT_GITHUB_SCOPE_NOT_CONFIGURED")
        from mvp.archivos.origen import git, entorno_git
        try:
            env = entorno_git(lambda: control.credencial("github", banco, estricto=True),
                              "maxbry123-commits")
            if not env.get("MOTOR_TOKEN"):
                raise ContractError("GITHUB_TOKEN_NO_DISPONIBLE")
            remote = git(["ls-remote",
                "https://github.com/maxbry123-commits/router-universal-router-inteligente-.git",
                "refs/heads/main"], env=env, espera=40)
            sha = remote.split()[0]
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ContractError("GITHUB_HEAD_NOT_VERIFIED")
            return sha
        except ContractError:
            raise
        except Exception:
            # Never reveal tokens, git stderr, or credential helper output.
            raise ContractError("GITHUB_HEAD_UNAVAILABLE") from None

    def git_read_text(path):
        # Read GitHub source of truth directly, not the possibly stale HF
        # checkout. Reuse the existing bank's GitHub credential.
        import urllib.parse
        import urllib.request
        if not github_ready:
            raise ContractError("PROJECT_GITHUB_SCOPE_NOT_CONFIGURED")
        safe_target(path)
        encoded=urllib.parse.quote("chat-router/"+path,safe="/")
        url=("https://api.github.com/repos/maxbry123-commits/"
             "router-universal-router-inteligente-/contents/"+encoded+"?ref=main")
        try:
            token=control.credencial("github",banco,estricto=True)
            if not isinstance(token,str) or not token:
                raise ContractError("GITHUB_TOKEN_NO_DISPONIBLE")
            req=urllib.request.Request(url,headers={
                "Accept":"application/vnd.github+json",
                "Authorization":"Bearer "+token,
                "User-Agent":"YAIWES-N4-readback"})
            with urllib.request.urlopen(req,timeout=20) as response:
                if response.status!=200:
                    raise ContractError("GITHUB_READBACK_UNAVAILABLE")
                raw=response.read(1400000)
            data=json.loads(raw.decode("utf8"))
            if data.get("type")!="file" or data.get("encoding")!="base64":
                raise ContractError("GITHUB_FILE_READBACK_INVALID")
            payload=base64.b64decode(data["content"],validate=False)
            if len(payload)>1000000:
                raise ContractError("GITHUB_FILE_TOO_LARGE")
            return payload
        except ContractError:
            raise
        except Exception:
            # No provider error body or token is ever logged.
            raise ContractError("GITHUB_READBACK_UNAVAILABLE") from None

    def git_write_text(path, value, approval):
        # Validate untrusted model bytes before calling encode() or touching git.
        if not isinstance(value,str) or len(value.encode("utf8"))>512000:
            raise ContractError("WRITE_TEXT_TOO_LARGE_OR_INVALID")
        if not github_ready or not isinstance(approval,dict) or not approval.get("approved"):
            raise ContractError("BLOCKED_APPROVAL")
        if (approval.get("writer")!="N4" or not approval.get("actor")
                or not isinstance(approval.get("write_paths"),list)
                or any(scope not in project_row["write_paths"] for scope in approval["write_paths"])
                or not isinstance(approval.get("approved_content_sha256"),str)
                or approval["approved_content_sha256"]!=sha256(value.encode("utf8"))
                or not isinstance(approval.get("github_head"),str)
                or approval["github_head"]!=github_head()):
            raise ContractError("GITHUB_HEAD_CHANGED_REAPPROVAL_REQUIRED")
        if not isinstance(value,str) or len(value.encode("utf8"))>512000:
            raise ContractError("WRITE_TEXT_TOO_LARGE")
        if not any(path==scope or path.startswith(scope.rstrip("/")+"/")
                   for scope in project_row["write_paths"]):
            raise ContractError("SUPERVISOR_SCOPE_VIOLATION")
        # The Ricardo reference motor never receives this GitHub capability.
        # Its vetted DAG/path admission policy is checked here BEFORE the
        # existing authenticated writer publishes any bytes.
        from .ricardo_plan_guard import inspect_plan, RicardoGuardError
        policy_path = (root / "Loop cola wachdog" / "Loop" /
                       "referencia_ricardo" / "allowed_ops.json")
        try:
            policy = json.loads(policy_path.read_text(encoding="utf8"))
            policy["max_text_chars"] = 512000
            inspection = inspect_plan({"ops": [{
                "id": "n4_write", "op": "write_text", "path": path,
                "text": value, "depends_on": []}]}, policy,
                allowed_write_paths=approval["write_paths"])
            if not inspection.get("requires_n4_approval"):
                raise RicardoGuardError("WRITER_N4_REQUIRED")
        except (RicardoGuardError, OSError, ValueError, KeyError, TypeError):
            raise ContractError("RICARDO_PLAN_GUARD_BLOCKED") from None
        from mvp.archivos.destino_git import publicar
        with tempfile.TemporaryDirectory(prefix="n4-git-write-") as tmp:
            source = Path(tmp)/Path(path).name
            source.write_text(value,encoding="utf8")
            target_dir=Path("chat-router")/Path(path).parent
            try:
                published=publicar(source,
                  "git:maxbry123-commits/router-universal-router-inteligente-@main/"+target_dir.as_posix(),
                  "YAIWES N4 approved "+project+" "+loop,
                  token_fn=lambda:control.credencial("github",banco,estricto=True),
                  sobrescribir=True, expected_head=approval["github_head"])
            except Exception:
                raise ContractError("GITHUB_WRITE_NOT_VERIFIED") from None
        committed=github_head()
        if not committed.startswith(str(published.get("commit",""))):
            raise ContractError("GITHUB_COMMIT_READBACK_MISMATCH")
        if git_read_text(path)!=value.encode("utf8"):
            raise ContractError("GITHUB_FILE_READBACK_MISMATCH")
        return {"ok":True,"evidence_ref":"git:"+committed+":"+sha256(value.encode("utf8")),
                "plan_sha256": inspection["plan_sha256"], "commit":committed}

    def tool(op, args, context):
        from .trigger_contract import WRITE_OPS
        if op in WRITE_OPS:
            if op != "write_text":
                raise ContractError("GITHUB_EMPTY_DIRECTORY_NOT_A_COMMIT")
            if not isinstance(args,dict):
                raise ContractError("BAD_TOOL_ARGS")
            path=args.get("path")
            if not isinstance(path,str):
                raise ContractError("BAD_TOOL_ARGS")
            safe_target(path)
            return git_write_text(path,args.get("text"),context.get("authorization"))
        if not isinstance(args, dict):
            raise ContractError("BAD_TOOL_ARGS")
        target = safe_target(args["path"]) if "path" in args else root
        if context.get("readback_write") is True and op == "read_text":
            raw = git_read_text(args["path"])
            try:
                value=raw.decode("utf8")
            except UnicodeError:
                raise ContractError("GITHUB_READBACK_NOT_UTF8")
            return {"ok":True,"text":value,"evidence_ref":"gitfile:"+sha256(raw)}
        if op == "inspect_workspace":
            names = sorted(p.name for p in root.iterdir())[:100]
            return {"ok": True, "entries": names,
                    "evidence_ref": "fs:" + sha256(canonical(names))}
        if op == "finish":
            return {"ok": True, "evidence_ref": "dsl:finish"}
        if op not in ("read_text", "verify_exists", "verify_contains"):
            raise ContractError("TOOL_NOT_AVAILABLE")
        if op == "verify_exists":
            if not target.is_file():
                return {"ok": False, "evidence_ref": "fs:missing:" + sha256(str(target).encode())}
            # X-Ray: file existence alone is not immutable evidence of its contents.
            # Stream the hash without loading unbounded files into RAM.
            digest = hashlib.sha256()
            with target.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    digest.update(chunk)
            return {"ok": True, "evidence_ref": "fs:" + digest.hexdigest()}
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
                or not github_ready or not row.get("github_head")
                or not isinstance(row.get("approved_content_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", row["approved_content_sha256"])
                or row["github_head"] != github_head()
                or time.time() - row.get("timestamp", 0) > 1800):
            return {"approved": False}
        return row

    def research(query):
        # Cross-building calls MUST use the existing Harness HTTP /invoke.
        # The Harness owns external research, not the browser or model.
        from mvp import harness_client
        try:
            credential=banco.leer("RIU_API_KEY")
            out=harness_client._enviar("invoke",{
                "tool":"mechanico_buscar","args":{"query":query}},credential)
        except Exception:
            raise ContractError("HARNESS_RESEARCH_UNAVAILABLE") from None
        if (not isinstance(out,dict) or out.get("status")!="ok"
                or not isinstance(out.get("result"),list)
                or len(out["result"])!=10):
            raise ContractError("HARNESS_RESEARCH_NOT_VERIFIED")
        return out["result"]

    ports=HostPorts(load,save,constitution,anchor,facts,queue_claim,
                    model,tool,approve,queue_complete,queue_create,
                    store.control,store.get,store.events,roles_resolve,
                    False,store.skip_dsl_task)
    ports.research=research
    ports.github_head=github_head if github_ready else None
    ports.can_write=github_ready
    return ports
