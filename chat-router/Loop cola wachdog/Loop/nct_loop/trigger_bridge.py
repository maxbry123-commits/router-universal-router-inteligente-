"""YAIWES trigger adapter: authenticated existing Harness, CIT-50 and Watchdog48."""
from __future__ import annotations
import inspect
import time
from .trigger_contract import ContractError, _id, canonical, sha256, validate_contract, validate_loop
from .trigger_engine import TriggerEngine, HostPorts

async def _invoke(cb, *args):
    if not callable(cb):
        raise ContractError("PORT_NOT_CONNECTED")
    v = cb(*args)
    return await v if inspect.isawaitable(v) else v

def validate_loop_meta(meta, *, loop_id, contracts):
    """Extend the persisted loop configuration, keeping old loop_save payloads valid."""
    if not isinstance(meta, dict) or set(meta) - {"name", "objective_ref", "notes",
            "depends_on_loops", "segments", "verify_on_end", "next_loop_id"}:
        raise ContractError("LOOP_META_INVALID")
    if any(not isinstance(v, str) or len(v) > 1500
           for k, v in meta.items() if k not in
           ("depends_on_loops", "segments", "verify_on_end")):
        raise ContractError("LOOP_META_INVALID")
    deps = meta.get("depends_on_loops", [])
    if not isinstance(deps, list) or len(deps) > 100 or any(
            not isinstance(x, str) or len(x) > 80 for x in deps):
        raise ContractError("LOOP_META_INVALID")
    if "verify_on_end" in meta and type(meta["verify_on_end"]) is not bool:
        raise ContractError("VERIFY_ON_END_INVALID")
    next_id = meta.get("next_loop_id")
    if next_id:
        _id(next_id, "next_loop_id")
        if next_id == loop_id:
            raise ContractError("NEXT_LOOP_CYCLE")
    segments = meta.get("segments", [])
    if not isinstance(segments, list) or len(segments) > 100:
        raise ContractError("SEGMENTS_INVALID")
    ids, assigned = set(), set()
    known = {c["id"] for c in contracts}
    for seg in segments:
        if not isinstance(seg, dict) or set(seg) != {"id", "name", "trigger_ids"}:
            raise ContractError("SEGMENT_INVALID")
        sid = _id(seg["id"], "segment_id")
        if sid in ids or not isinstance(seg["name"], str) or not (1 <= len(seg["name"]) <= 150):
            raise ContractError("SEGMENT_DUPLICATE_OR_NAME_INVALID")
        ids.add(sid)
        triggers = seg["trigger_ids"]
        if not isinstance(triggers, list) or len(triggers) > 100 or any(
                not isinstance(t, str) or t not in known or t in assigned for t in triggers):
            raise ContractError("SEGMENT_TRIGGERS_INVALID")
        if len(set(triggers)) != len(triggers):
            raise ContractError("SEGMENT_TRIGGERS_INVALID")
        assigned.update(triggers)
    return meta


class TriggerBridge:
    def __init__(self, ports: HostPorts):
        self.ports = ports
        self.engine = TriggerEngine(ports)

    async def _prior(self, project, loop, contract, contracts):
        by = {c["id"]: c for c in contracts}
        result = {}
        current_const, _ = await self.engine._constitution()
        for dep in contract.get("depends_on", []):
            source = by.get(dep)
            if source is None:
                continue
            receipt = await _invoke(self.ports.load, f"dsl:{project}:{loop}:{dep}")
            if (not isinstance(receipt, dict) or receipt.get("status") != "PASS"
                    or receipt.get("contract_sha256") != sha256(canonical(source))
                    or receipt.get("constitution_sha256") != current_const
                    or not isinstance(receipt.get("anchor_receipts"), dict)):
                continue
            good = True
            for ref, recorded in receipt["anchor_receipts"].items():
                a = await _invoke(self.ports.anchor, ref)
                if not isinstance(recorded, dict) or not isinstance(a, dict) or not isinstance(a.get("bytes"), bytes) or sha256(a["bytes"]) != recorded.get("sha256"):
                    good = False
                    break
            if good:
                result[dep] = "PASS"
        return result

    async def _handoff_verified(self, *, project, loop, state, server_context):
        """Transition into an ALREADY configured LOOP with durable evidence only.
        Uses existing HF state and CIT-50 queue; no autonomous model authority.
        """
        meta = state.get("loop_meta") or {}
        next_id = meta.get("next_loop_id")
        if not next_id:
            return {"status": "NO_NEXT_LOOP", "dispatched": False}
        if meta.get("verify_on_end", True):
            return {"status": "REVIEW_REQUIRED", "dispatched": False, "next_loop_id": next_id}
        qid = state.get("queue_id")
        queue = await _invoke(self.ports.queue_status, qid)
        if not isinstance(queue, dict) or queue.get("status") != "completed":
            return {"status": "QUEUE_NOT_COMPLETED", "dispatched": False}
        rows = {x["id"]: x for x in queue.get("tasks", []) if isinstance(x, dict) and x.get("id")}
        constitution, _ = await self.engine._constitution()
        contracts = state.get("contracts", [])
        # A queue receipt alone isn't proof. Compare immutable contract,
        # Constitution and source anchors before enabling the next LOOP.
        all_enabled = [c["id"] for c in contracts if c.get("enabled")]
        if not all_enabled:
            return {"status": "ALL_TRIGGERS_OFF_NO_HANDOFF", "dispatched": False}
        verified = await self._prior(project, loop, {"depends_on": all_enabled}, contracts)
        for c in contracts:
            row = rows.get(c["id"])
            if not row:
                return {"status": "MISSING_QUEUE_RECEIPT", "dispatched": False}
            if not c.get("enabled"):
                if row.get("status") != "skipped":
                    return {"status": "OFF_SLOT_NOT_SKIPPED", "dispatched": False}
                continue
            if row.get("status") == "succeeded" and c["id"] in verified and row.get("receipt_id"):
                continue
            rec = await _invoke(self.ports.load, f"dsl:{project}:{loop}:{c['id']}")
            if (row.get("status") == "skipped" and isinstance(rec, dict)
                    and rec.get("status") == "NOT_APPLICABLE"
                    and rec.get("contract_sha256") == sha256(canonical(c))
                    and rec.get("constitution_sha256") == constitution):
                continue
            return {"status": "UNVERIFIED_CURRENT_LOOP", "dispatched": False, "trigger_id": c["id"]}
        successor = await _invoke(self.ports.load, f"dsl-config:{project}:{next_id}")
        if not isinstance(successor, dict) or not successor.get("contracts"):
            return {"status": "NEXT_LOOP_NOT_CONFIGURED", "dispatched": False, "next_loop_id": next_id}
        from .trigger_contract import validate_loop
        validate_loop(successor["contracts"])
        deps = (successor.get("loop_meta") or {}).get("depends_on_loops", [])
        if loop not in deps:
            return {"status": "NEXT_LOOP_DEPENDENCY_NOT_LINKED", "dispatched": False}
        if successor.get("queue_id"):
            # Resume an already-started successor after process restart iff
            # the exact durable handoff proof exists and matches the queue.
            previous = await _invoke(self.ports.load, f"dsl-handoff:{project}:{loop}:{next_id}")
            if (isinstance(previous, dict) and previous.get("status") == "HANDOFF_STARTED"
                    and previous.get("to_loop") == next_id and previous.get("from_loop") == loop
                    and previous.get("queue_id") == successor["queue_id"]
                    and previous.get("constitution_sha256") == constitution):
                return {"status": "HANDOFF_ALREADY_STARTED", "dispatched": True,
                        "next_loop_id": next_id, "queue_id": successor["queue_id"]}
            return {"status": "NEXT_LOOP_RECONCILIATION_REQUIRED", "dispatched": False,
                    "next_loop_id": next_id}
        started = await self.handle("dsl_control", {
            "project_id": project, "loop_id": next_id, "op": "start",
            "expected_revision": successor["revision"]}, server_context=server_context)
        if not started.get("ok") or not started.get("queue_id"):
            return {"status": "NEXT_LOOP_START_FAILED", "dispatched": False, "detail": started}
        record = {"from_loop": loop, "to_loop": next_id,
                  "queue_id": started["queue_id"],
                  "from_config_sha256": sha256(canonical(state)),
                  "to_config_sha256": sha256(canonical(successor)),
                  "constitution_sha256": constitution, "status": "HANDOFF_STARTED"}
        key = f"dsl-handoff:{project}:{loop}:{next_id}"
        # The successor was already durably STARTED. Read back the handoff
        # before we report dispatched=True, never imply false success.
        if await _invoke(self.ports.save, key, record) is not True:
            return {"status": "HANDOFF_CHECKPOINT_UNCERTAIN", "dispatched": False,
                    "next_loop_id": next_id}
        check = await _invoke(self.ports.load, key)
        if check != record:
            return {"status": "HANDOFF_READBACK_MISMATCH", "dispatched": False,
                    "next_loop_id": next_id}
        return {"status": "HANDOFF_STARTED", "dispatched": True,
                "next_loop_id": next_id, "queue_id": started["queue_id"]}

    async def dispatch_ready(self, *, project, loop, state, server_context, max_steps=100):
        """Continue an existing DSL queue on this very PluginHost executor.
        The CIT-50 claim is the single-executor gate; no second queue/daemon.
        Each checkpoint and PASS is checked by the existing TriggerEngine.
        """
        if type(max_steps) is not int or not 1 <= max_steps <= 100:
            raise ContractError("BAD_DISPATCH_LIMIT")
        qid = state.get("queue_id")
        if not qid:
            raise ContractError("LOOP_NOT_STARTED")
        contracts = state.get("contracts", [])
        completed = []
        for _ in range(max_steps):
            q = await _invoke(self.ports.queue_status, qid)
            if not isinstance(q, dict) or not isinstance(q.get("tasks"), list):
                raise ContractError("QUEUE_NOT_CONNECTED")
            if q.get("status") != "running":
                output = {"ok": q.get("status") == "completed", "status": q.get("status", "BLOCKED").upper(),
                          "queue_id": qid, "processed": completed, "queue_status": q.get("status")}
                if q.get("status") == "completed":
                    output["handoff"] = await self._handoff_verified(project=project, loop=loop,
                        state=state, server_context=server_context)
                return output
            rows = {t["id"]: t for t in q["tasks"] if isinstance(t, dict) and isinstance(t.get("id"), str)}
            if any(t.get("status") in ("running", "needs_reconciliation") for t in rows.values()):
                return {"ok": False, "status": "BLOCKED", "error": "QUEUE_BUSY_OR_RECONCILIATION",
                        "queue_id": qid, "processed": completed}
            eligible = None
            previous = {}
            for c in contracts:
                t = rows.get(c["id"])
                if not c.get("enabled") or not t or t.get("status") != "pending":
                    continue
                p = await self._prior(project, loop, c, contracts)
                if all(p.get(dep) == "PASS" for dep in c.get("depends_on", [])):
                    eligible, previous = c, p
                    break
            if eligible is None:
                return {"ok": False, "status": "BLOCKED", "error": "NO_ELIGIBLE_TRIGGER",
                        "queue_id": qid, "processed": completed,
                        "pending": [t["id"] for t in rows.values() if t.get("status") == "pending"]}
            result = await self.engine.run_once(project_id=project, contract=eligible,
                role_pairs=state.get("role_pairs", {}), host_context=server_context, previous=previous)
            if not isinstance(result, dict):
                raise ContractError("ENGINE_RESULT_INVALID")
            status = result.get("status")
            if status == "NOT_APPLICABLE":
                if not callable(self.ports.queue_skip):
                    raise ContractError("QUEUE_SKIP_NOT_CONNECTED")
                skipped = await _invoke(self.ports.queue_skip, qid, eligible["id"], "NOT_APPLICABLE")
                if not isinstance(skipped, dict) or skipped.get("skipped") is not True:
                    raise ContractError("QUEUE_SKIP_FAILED")
                completed.append({"id": eligible["id"], "status": "NOT_APPLICABLE"})
                continue
            if status != "PASS" or result.get("ok") is not True or result.get("replayed"):
                return {"ok": False, "status": "BLOCKED", "error": result.get("error") or
                        ("REPLAY_RECONCILIATION_REQUIRED" if result.get("replayed") else status or "ENGINE_FAILED"),
                        "queue_id": qid, "processed": completed, "failed_trigger": eligible["id"]}
            verified_q = await _invoke(self.ports.queue_status, qid)
            verified = next((x for x in verified_q.get("tasks", []) if x.get("id") == eligible["id"]), None)
            if not verified or verified.get("status") != "succeeded" or not verified.get("receipt_id"):
                raise ContractError("QUEUE_COMPLETION_STATE_MISMATCH")
            completed.append({"id": eligible["id"], "status": "PASS", "receipt_id": verified["receipt_id"]})
        final = await _invoke(self.ports.queue_status, qid)
        if final.get("status") != "running":
            output = {"ok": final.get("status") == "completed",
                      "status": final.get("status", "BLOCKED").upper(), "queue_id": qid,
                      "processed": completed, "queue_status": final.get("status")}
            if final.get("status") == "completed":
                output["handoff"] = await self._handoff_verified(project=project, loop=loop,
                    state=state, server_context=server_context)
            return output
        return {"ok": True, "status": "LIMIT_REACHED", "queue_id": qid,
                "processed": completed, "next": "CALL_DISPATCH_AGAIN"}

    async def handle(self, action, request, *, server_context=None):
        try:
            if action not in {"dsl_config", "dsl_control", "dsl_estado"}:
                raise ContractError("UNKNOWN_ACTION")
            if not isinstance(request, dict):
                raise ContractError("BAD_REQUEST")
            if not isinstance(server_context, dict) or server_context.get("authenticated") is not True:
                raise ContractError("HOST_AUTH_REQUIRED")
            if any(k in request for k in ("authenticated_by_host", "host_context", "previous")):
                raise ContractError("UNTRUSTED_SERVER_FIELD")
            project = _id(request.get("project_id"), "project_id")
            loop = _id(request.get("loop_id"), "loop_id")
            if server_context.get("project_id") != project:
                raise ContractError("PROJECT_SCOPE_MISMATCH")
            key = f"dsl-config:{project}:{loop}"
            state = await _invoke(self.ports.load, key)
            if state is None:
                state = {"revision": 0, "contracts": [], "role_pairs": {}, "history": []}
            if not isinstance(state, dict):
                raise ContractError("STATE_INVALID")
            op = request.get("op")
            if action == "dsl_estado":
                if op in ("get", "health", "flags"):
                    qid = state.get("queue_id")
                    queue = await _invoke(self.ports.queue_status, qid) if qid else None
                    statuses = {}
                    flags = []
                    for c in state.get("contracts", []):
                        receipt = await _invoke(self.ports.load, f"dsl:{project}:{loop}:{c['id']}")
                        info = {"status": (receipt or {}).get("status", "QUEUED" if c["enabled"] else "OFF"),
                                "flags": (receipt or {}).get("flags", []),
                                "contract_sha256": sha256(canonical(c)),
                                "depends_on": c.get("depends_on", []),
                                "source_ref": c["source"]["document_ref"]}
                        statuses[c["id"]] = info
                        flags.extend(info["flags"])
                    segments = state.get("loop_meta", {}).get("segments", [])
                    phase_index = next((i for i, seg in enumerate(segments) if any(
                        statuses.get(tid, {}).get("status") not in
                        ("PASS", "NOT_APPLICABLE", "OFF")
                        for tid in seg.get("trigger_ids", []))), len(segments))
                    return {"ok": True, "status": "PASS", "project_id": project, "loop_id": loop,
                            "phase_index": phase_index, "verify_on_end": state.get("loop_meta", {}).get("verify_on_end", True),
                            "revision": state["revision"], "contracts": state["contracts"],
                            "role_pairs": state["role_pairs"], "history": state["history"],
                            "loop_meta": state.get("loop_meta", {}), "queue": queue,
                            "watchdog_id": state.get("watchdog_id"), "triggers": statuses,
                            "flags": flags, "event_cursor": state["revision"]}
                if op == "gaps":
                    ledger = await _invoke(self.ports.load, f"dsl-gaps:{project}") or {}
                    return {"ok": True, "status": "PASS", "project_id": project,
                            "gaps": ledger.get("gaps", []), "revision": ledger.get("revision", 0)}
                if op == "gap_sources":
                    ledger = await _invoke(self.ports.load, f"dsl-gaps:{project}") or {}
                    item = next((g for g in ledger.get("gaps", []) if g["gap_id"] ==
                                 request.get("gap_id")), None)
                    if not item:raise ContractError("GAP_NOT_FOUND")
                    return {"ok": True, "status": "PASS",
                            "research": item.get("research", []), "selected": item.get("selected")}
                if op == "events":
                    if not state.get("queue_id"):
                        return {"ok": True, "status": "PASS", "events": []}
                    return {"ok": True, "status": "PASS", "events": await _invoke(
                        self.ports.queue_events, state["queue_id"], max(0, int(request.get("since_event") or 0)))}
                if op == "checkpoint":
                    tid = _id(request.get("trigger_id"), "trigger_id")
                    return {"ok": True, "status": "PASS",
                            "checkpoint": await _invoke(self.ports.load, f"dsl:{project}:{loop}:{tid}")}
                raise ContractError("STATE_OP_UNSUPPORTED")
            if action == "dsl_config":
                if op == "contract_validate":
                    c = request.get("contract")
                    validate_contract(c)
                    return {"ok": True, "status": "PASS", "contract_sha256": sha256(canonical(c))}
                if request.get("expected_revision") != state["revision"]:
                    raise ContractError("REVISION_CONFLICT")
                new = dict(state)
                new["contracts"] = [dict(c) for c in state.get("contracts", [])]
                new["history"] = list(state.get("history", []))
                new["role_pairs"] = dict(state.get("role_pairs", {}))
                if op == "trigger_upsert":
                    c = request.get("contract")
                    validate_contract(c)
                    if c["loop_id"] != loop:
                        raise ContractError("LOOP_MISMATCH")
                    old = next((c0 for c0 in new["contracts"] if c0["id"] == c["id"]), None)
                    if old:
                        new["history"].append({"id": old["id"], "sha256": sha256(canonical(old)), "reason": "REPLACED"})
                    new["contracts"] = [c0 for c0 in new["contracts"] if c0["id"] != c["id"]] + [c]
                elif op in ("trigger_toggle", "note_update", "anchor_bind", "trigger_remove"):
                    tid = request.get("trigger_id")
                    old = next((c for c in new["contracts"] if c["id"] == tid), None)
                    if old is None:
                        raise ContractError("TRIGGER_NOT_FOUND")
                    new["history"].append({"id": tid, "sha256": sha256(canonical(old)), "reason": op})
                    if op == "trigger_remove":
                        new["contracts"] = [c for c in new["contracts"] if c["id"] != tid]
                    else:
                        updated = dict(old)
                        if op == "trigger_toggle":
                            if type(request.get("enabled")) is not bool:
                                raise ContractError("BAD_ENABLED")
                            updated["enabled"] = request["enabled"]
                        elif op == "note_update":
                            updated["note"] = request.get("note", "")
                        else:
                            updated["attachments"] = request.get("anchor_refs")
                        validate_contract(updated)
                        new["contracts"] = [updated if c["id"] == tid else c for c in new["contracts"]]
                elif op == "loop_save":
                    meta = request.get("loop_meta")
                    new["loop_meta"] = validate_loop_meta(meta, loop_id=loop,
                        contracts=new["contracts"])
                elif op == "roles_save":
                    roles = request.get("role_pairs")
                    if not isinstance(roles, dict) or set(roles) - {"arquitecto", "auditor", "ejecutor_codigo", "frontend", "refactor_revision"}:
                        raise ContractError("BAD_ROLE_PAIRS")
                    for row in roles.values():
                        if not isinstance(row, dict) or not row.get("model_id") or not row.get("agent_id"):
                            raise ContractError("BAD_ROLE_PAIR")
                    checked = await _invoke(self.ports.roles_resolve, roles)
                    if not isinstance(checked, dict):
                        raise ContractError("ROLE_RESOLVER_NOT_CONNECTED")
                    new["role_pairs"] = checked
                else:
                    raise ContractError("CONFIG_OP_UNSUPPORTED")
                if new["contracts"]:
                    validate_loop(new["contracts"])
                if state.get("queue_id"):
                    raise ContractError("LOOP_CONFIG_FROZEN_AFTER_START")
                new["revision"] += 1
                if await _invoke(self.ports.save, key, new) is not True:
                    raise ContractError("CHECKPOINT_NOT_DURABLE")
                return {"ok": True, "status": "PASS", "revision": new["revision"],
                        "count": len(new["contracts"]), "config_sha256": sha256(canonical(new))}
            if op == "gap_collect":
                if not state.get("queue_id"):raise ContractError("LOOP_NOT_STARTED")
                from .repair import gap_events
                q = await _invoke(self.ports.queue_status, state["queue_id"])
                checkpoints = {c["id"]:await _invoke(self.ports.load,
                    f"dsl:{project}:{loop}:{c['id']}") for c in state.get("contracts",[])}
                observed=gap_events(project,loop,state.get("contracts",[]),checkpoints,q)
                key_gaps=f"dsl-gaps:{project}"
                old=await _invoke(self.ports.load,key_gaps) or {"revision":0,"gaps":[]}
                existing={item["gap_id"]:item for item in old["gaps"]}
                for item in observed:
                    if item["gap_id"] not in existing:
                        existing[item["gap_id"]]=dict(item,status="OPEN",research=[])
                if len(existing)>250:raise ContractError("GAP_LEDGER_LIMIT")
                new={"revision":old["revision"]+1,"gaps":list(existing.values())}
                if await _invoke(self.ports.save,key_gaps,new) is not True:
                    raise ContractError("GAPS_CHECKPOINT_NOT_DURABLE")
                if await _invoke(self.ports.load,key_gaps)!=new:
                    raise ContractError("GAPS_READBACK_FAILED")
                return {"ok":True,"status":"PASS","project_id":project,"total":len(existing),
                        "new":len(existing)-len(old["gaps"]),"revision":new["revision"]}
            if op in ("gap_research","gap_select"):
                key_gaps=f"dsl-gaps:{project}"
                old=await _invoke(self.ports.load,key_gaps)
                if not isinstance(old,dict):raise ContractError("GAPS_NOT_COLLECTED")
                gaps=[dict(item) for item in old["gaps"]]
                item=next((g for g in gaps if g["gap_id"]==request.get("gap_id")),None)
                if not item:raise ContractError("GAP_NOT_FOUND")
                if op=="gap_research":
                    source=getattr(self.ports,"research",None)
                    candidates=await _invoke(source,item["code"])
                    if not isinstance(candidates,list) or len(candidates)!=10:
                        raise ContractError("RESEARCH_INCOMPLETE")
                    item["research"]=candidates
                    item["status"]="RESEARCHED_UNVERIFIED"
                else:
                    selected=request.get("selected_url")
                    matches=[s for s in item.get("research",[]) if s.get("url")==selected
                        and s.get("status")=="SOURCE_FOUND_UNVERIFIED"]
                    if len(matches)!=1:raise ContractError("SELECTION_NOT_IN_RESEARCH")
                    item["selected"]={"url":selected,"sha256":matches[0]["sha256"]}
                    item["status"]="SELECTED_NEEDS_CONTRACT_APPROVAL"
                new={"revision":old["revision"]+1,"gaps":gaps}
                if await _invoke(self.ports.save,key_gaps,new) is not True:
                    raise ContractError("GAPS_CHECKPOINT_NOT_DURABLE")
                if await _invoke(self.ports.load,key_gaps)!=new:
                    raise ContractError("GAPS_READBACK_FAILED")
                return {"ok":True,"status":item["status"],"gap_id":item["gap_id"],
                        "revision":new["revision"],"executable":False}
            if op == "run_ready":
                return await self.dispatch_ready(project=project, loop=loop, state=state,
                    server_context=server_context, max_steps=request.get("max_steps", 100))
            if op == "start":
                if request.get("expected_revision") != state["revision"]:
                    raise ContractError("REVISION_CONFLICT")
                if state.get("queue_id"):
                    raise ContractError("LOOP_ALREADY_STARTED")
                contracts = state.get("contracts") or []
                validate_loop(contracts)
                await self.engine._constitution()
                duration = request.get("duration_minutes", 60)
                if type(duration) is not int or not 10 <= duration <= 2880:
                    raise ContractError("WATCHDOG_DURATION_INVALID")
                q = await _invoke(self.ports.queue_create, project, loop, contracts, duration)
                if not isinstance(q, dict) or not q.get("queue_id"):
                    raise ContractError("QUEUE_NOT_CONNECTED")
                new = dict(state, queue_id=q["queue_id"],
                           watchdog_id=q.get("watchdog_id"), revision=state["revision"] + 1,
                           session=server_context.get("sesion","web-general"))
                try:
                    if await _invoke(self.ports.save, key, new) is not True:
                        raise ContractError("QUEUE_CREATED_CHECKPOINT_FAILED")
                except Exception:
                    try:
                        await _invoke(self.ports.queue_control, q["queue_id"], "cancel")
                    except Exception:
                        raise ContractError("QUEUE_ORPHAN_RECONCILIATION_REQUIRED")
                    raise ContractError("QUEUE_CREATED_CHECKPOINT_FAILED")
                return {"ok": True, "status": "QUEUED", "queue_id": q["queue_id"],
                        "watchdog_id": q.get("watchdog_id"), "revision": new["revision"]}
            if op in ("pause", "resume", "cancel"):
                if not state.get("queue_id"):
                    raise ContractError("LOOP_NOT_STARTED")
                q = await _invoke(self.ports.queue_control, state["queue_id"], op)
                if not isinstance(q, dict) or not q.get("status"):
                    raise ContractError("QUEUE_CONTROL_NOT_WIRED")
                return {"ok": True, "status": q["status"], "queue": q}
            if op == "approve":
                if (request.get("command") != "/aprobar" or not server_context.get("operator_id")
                        or not server_context.get("director_confirmed")):
                    raise ContractError("BLOCKED_APPROVAL")
                tid = request.get("trigger_id")
                contract = next((c for c in state["contracts"] if c["id"] == tid), None)
                if not contract:
                    raise ContractError("TRIGGER_NOT_FOUND")
                from .trigger_contract import WRITE_OPS
                if not any(s["kind"] == "TOOL" and s.get("tool") in WRITE_OPS for s in contract["steps"]):
                    raise ContractError("APPROVAL_NOT_APPLICABLE")
                constitutional_sha, _ = await self.engine._constitution()
                if self.ports.can_write is not True or not callable(getattr(self.ports, "github_head", None)):
                    raise ContractError("AUTHORIZED_GITHUB_WRITER_NOT_CONNECTED")
                # N4 approves an exact diff/content SHA, not an unknown future
                # model output. The human must review the proposed bytes first.
                import re
                approved_sha = request.get("approved_content_sha256")
                if not isinstance(approved_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", approved_sha):
                    raise ContractError("N4_REQUIRES_REVIEWED_CONTENT_SHA256")
                github_head = await _invoke(self.ports.github_head)
                if not isinstance(github_head, str) or len(github_head) != 40:
                    raise ContractError("GITHUB_HEAD_NOT_VERIFIED")
                record = {"approved": True, "writer": "N4", "actor": server_context["operator_id"],
                          "approved_content_sha256": approved_sha,
                          "github_head": github_head,
                          "constitution_sha256": constitutional_sha,
                          "contract_sha256": sha256(canonical(contract)),
                          "write_paths": contract["execution"]["write_paths"],
                          "timestamp": int(time.time())}
                record["approval_ref"] = "approval:" + sha256(canonical(record))
                if await _invoke(self.ports.save, f"dsl-approval:{project}:{loop}:{tid}", record) is not True:
                    raise ContractError("CHECKPOINT_NOT_DURABLE")
                return {"ok": True, "status": "APPROVED", "approval_ref": record["approval_ref"]}
            if op == "next_loop":
                current_sha, _ = await self.engine._constitution()
                done = []
                for c in state.get("contracts", []):
                    r = await _invoke(self.ports.load, f"dsl:{project}:{loop}:{c['id']}")
                    if (not isinstance(r, dict) or r.get("status") != "PASS"
                            or r.get("contract_sha256") != sha256(canonical(c))
                            or r.get("constitution_sha256") != current_sha
                            or not isinstance(r.get("anchor_receipts"), dict)):
                        continue
                    valid = True
                    for ref, old in r["anchor_receipts"].items():
                        a = await _invoke(self.ports.anchor, ref)
                        if not isinstance(a, dict) or not isinstance(a.get("bytes"), bytes) or sha256(a["bytes"]) != old.get("sha256"):
                            valid = False
                    if valid:
                        done.append(c["id"])
                eligible = [c["id"] for c in state["contracts"] if c["id"] not in done
                            and c.get("enabled") and set(c.get("depends_on", [])) <= set(done)]
                return {"ok": True, "status": "PASS", "completed": done, "eligible": eligible,
                        "dispatched": False}
            if op == "retry_safe":
                raise ContractError("RETRY_REQUIRES_RECONCILIATION")
            if op != "run_one":
                raise ContractError("CONTROL_OP_UNSUPPORTED")
            if not state.get("queue_id"):
                raise ContractError("LOOP_NOT_STARTED")
            q = await _invoke(self.ports.queue_status, state["queue_id"])
            if not isinstance(q, dict) or q.get("status") != "running":
                raise ContractError("QUEUE_NOT_RUNNING")
            tid = request.get("trigger_id")
            c = next((c for c in state["contracts"] if c["id"] == tid), None)
            if c is None:
                raise ContractError("TRIGGER_NOT_FOUND")
            previous = await self._prior(project, loop, c, state["contracts"])
            return await self.engine.run_once(project_id=project, contract=c,
                role_pairs=state["role_pairs"], host_context=server_context, previous=previous)
        except ContractError as e:
            return {"ok": False, "status": "BLOCKED", "error": e.code, "detail": e.detail}
