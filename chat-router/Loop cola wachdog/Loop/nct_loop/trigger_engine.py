"""Deterministic single-trigger executor, reusing existing backend ports."""
from __future__ import annotations
import inspect
import json
import asyncio
from dataclasses import dataclass
from typing import Callable
from .trigger_contract import (ContractError, READ_OPS, WRITE_OPS, canonical,
    check_condition, ordered_steps, sha256, validate_contract)

async def _call(fn, *args):
    if not callable(fn):
        raise ContractError("PORT_NOT_CONNECTED")
    result = fn(*args)
    return await result if inspect.isawaitable(result) else result

@dataclass
class HostPorts:
    load: Callable
    save: Callable
    constitution: Callable
    anchor: Callable
    facts: Callable
    queue_claim: Callable
    model: Callable
    tool: Callable
    approve: Callable
    queue_complete: Callable | None = None
    queue_create: Callable | None = None
    queue_control: Callable | None = None
    queue_status: Callable | None = None
    queue_events: Callable | None = None
    roles_resolve: Callable | None = None
    can_write: bool = True
    queue_skip: Callable | None = None

class TriggerEngine:
    def __init__(self, ports: HostPorts):
        self.p = ports

    async def _save(self, key: str, data: dict):
        if await _call(self.p.save, key, data) is not True:
            raise ContractError("CHECKPOINT_NOT_DURABLE")

    async def _constitution(self) -> tuple[str, dict]:
        packet = await _call(self.p.constitution)
        if (not isinstance(packet, dict) or packet.get("anchor_set_checked") is not True
                or not isinstance(packet.get("bytes"), bytes)
                or not isinstance(packet.get("overlay_bytes"), list)
                or any(not isinstance(b, bytes) for b in packet["overlay_bytes"])):
            raise ContractError("GOVERNANCE_PREPARE_NO_DISPONIBLE")
        try:
            data = json.loads(packet["bytes"].decode("utf8"))
        except (UnicodeError, ValueError) as e:
            raise ContractError("CONSTITUTION_INVALID") from e
        if (not isinstance(data, dict) or data.get("id") != "CONSTITUCION-YAIWES"
                or data.get("estado") != "ACTIVA" or data.get("modo") != "FAIL_CLOSED"
                or data.get("escritor_unico", {}).get("nodo") != "N4"):
            raise ContractError("CONSTITUTION_INVALID")
        digest = sha256(canonical(data) + b"".join(b"\nOVERLAY\n" + p for p in packet["overlay_bytes"]))
        return digest, data

    async def _failed(self, key, current, code, started=False, mutating=False):
        current.update(ok=False, status="NEEDS_RECONCILIATION" if mutating else "BLOCKED",
                       error=code, flags=[{"symbol": "FLAG", "reason": code}])
        if started:
            try:
                await self._save(key, current)
            except ContractError:
                current.update(status="NEEDS_RECONCILIATION", error="CHECKPOINT_NOT_DURABLE")
                return current
            # Close the already claimed existing CIT queue with a real FAIL
            # receipt; never leave an unverified task marked as succeeded.
            if current.get("claim_ref") and callable(self.p.queue_complete):
                try:
                    out = await _call(self.p.queue_complete, current["claim_ref"],
                                      {"verification": "FAIL", "error": code,
                                       "trigger_id": current["trigger_id"]})
                    if not isinstance(out, dict) or out.get("ok") is not True:
                        raise ContractError("QUEUE_COMPLETION_FAILED")
                    current["queue_receipt_ref"] = out.get("evidence_ref")
                    await self._save(key, current)
                except (ContractError, RuntimeError, OSError):
                    current.update(status="NEEDS_RECONCILIATION",
                                   error="QUEUE_COMPLETION_UNCERTAIN")
        return current

    async def run_once(self, *, project_id: str, contract: dict,
                       role_pairs: dict, host_context: dict, previous=None) -> dict:
        tid = str(contract.get("id", "?"))
        lid = str(contract.get("loop_id", "?"))
        key = f"dsl:{project_id}:{lid}:{tid}"
        current = dict(ok=False, status="BLOCKED", trigger_id=tid, loop_id=lid,
                       project_id=project_id, flags=[], receipts=[])
        started = False
        mutating = False
        try:
            validate_contract(contract)
            if not isinstance(host_context, dict) or host_context.get("authenticated") is not True:
                raise ContractError("HOST_AUTH_REQUIRED")
            constitution_sha, _ = await self._constitution()
            contract_sha = sha256(canonical(contract))
            current.update(constitution_sha256=constitution_sha, contract_sha256=contract_sha)
            saved = await _call(self.p.load, key)
            if isinstance(saved, dict) and saved.get("status") == "PASS" and saved.get("contract_sha256") == contract_sha:
                if saved.get("constitution_sha256") != constitution_sha:
                    raise ContractError("CONSTITUTION_CHANGED_DURING_TASK")
                for ref, old in saved.get("anchor_receipts", {}).items():
                    fresh = await _call(self.p.anchor, ref)
                    if not isinstance(fresh, dict) or not isinstance(fresh.get("bytes"), bytes) or sha256(fresh["bytes"]) != old["sha256"]:
                        raise ContractError("SOURCE_CHANGED_DURING_TASK", ref)
                steps = {s["id"]: s for s in contract["steps"]}
                for receipt in saved.get("receipts", []):
                    step = steps.get(receipt.get("step_id"))
                    if not step or step.get("tool") not in READ_OPS:
                        continue
                    observed = await _call(self.p.tool, step["tool"], step.get("args", {}),
                        {"project_id": project_id, "loop_id": lid, "trigger_id": tid,
                         "authorization": None, "constitution_sha256": constitution_sha})
                    if not isinstance(observed, dict) or observed.get("ok") is not True or observed.get("evidence_ref") != receipt.get("evidence_ref"):
                        raise ContractError("SOURCE_CHANGED_DURING_TASK")
                return {**saved, "replayed": True}
            if isinstance(saved, dict) and saved.get("status") in {"STARTED", "NEEDS_RECONCILIATION"}:
                raise ContractError("NEEDS_RECONCILIATION")
            if not contract["enabled"]:
                current.update(status="OFF", reason="OFF_BY_OPERATOR")
                await self._save(key, current)
                return current
            for dep in contract.get("depends_on", []):
                if (previous or {}).get(dep) != "PASS":
                    raise ContractError("BLOCKED_DEPENDENCY", dep)
            refs = {}
            references = list(contract.get("attachments", []))
            doc_ref = contract["source"].get("source_anchor_ref")
            if doc_ref and doc_ref not in references:
                references.append(doc_ref)
            source_context = {}
            for ref in references:
                data = await _call(self.p.anchor, ref)
                if (not isinstance(data, dict) or not isinstance(data.get("bytes"), bytes)
                        or sha256(data["bytes"]) != data.get("sha256") or not data.get("evidence_ref")):
                    raise ContractError("FUENTE_ANCLADA_NO_LEIBLE", ref)
                refs[ref] = {"sha256": data["sha256"], "evidence_ref": data["evidence_ref"], "length": len(data["bytes"])}
                if ref == doc_ref and data["sha256"] != contract["source"]["original_document_sha256"]:
                    raise ContractError("DOCUMENT_SHA_MISMATCH", ref)
                try:
                    txt = data["bytes"].decode("utf8")
                except UnicodeDecodeError:
                    continue
                if len(data["bytes"]) > 100_000:
                    raise ContractError("SOURCE_TOO_LARGE_NEEDS_SEGMENT")
                source_context[ref] = txt
            if len(canonical(source_context)) > 120_000:
                raise ContractError("SOURCE_TOO_LARGE_NEEDS_SEGMENT")
            facts = await _call(self.p.facts, project_id, lid)
            if not isinstance(facts, dict):
                raise ContractError("FACTS_UNAVAILABLE")
            verdict, reason = check_condition(contract.get("when", {"predicate": "always", "args": {}}), facts)
            if verdict == "BLOCKED":
                raise ContractError(reason)
            if verdict == "NOT_APPLICABLE":
                current.update(status="NOT_APPLICABLE", reason=reason, flags=[{"symbol": "NOTICE", "reason": reason}])
                await self._save(key, current)
                return current
            role = contract["role"]
            selection = role_pairs.get(role)
            if not isinstance(selection, dict) or not selection.get("model_id") or not selection.get("agent_id") or selection.get("available") is not True:
                raise ContractError("ROLE_PAIR_UNAVAILABLE")
            write_steps = [s for s in contract["steps"] if s["kind"] == "TOOL" and s.get("tool") in WRITE_OPS]
            approval = None
            if write_steps:
                if self.p.can_write is not True:
                    raise ContractError("AUTHORIZED_GITHUB_WRITER_NOT_CONNECTED")
                if contract["execution"]["tool_profile"] != "writer_n4" or role not in {"ejecutor_codigo", "frontend", "refactor_revision"}:
                    raise ContractError("WRITER_N4_REQUIRED")
                paths = contract["execution"]["write_paths"]
                allowed = host_context.get("write_paths")
                if not isinstance(allowed, list) or any(p not in allowed for p in paths):
                    raise ContractError("SUPERVISOR_SCOPE_VIOLATION")
                for step in write_steps:
                    path = step.get("args", {}).get("path")
                    if not path or not any(path == p or path.startswith(p.rstrip("/") + "/") for p in paths):
                        raise ContractError("PATH_OUT_OF_SCOPE")
                approval = await _call(self.p.approve, {"project_id": project_id,
                    "loop_id": lid, "trigger_id": tid, "writer": "N4",
                    "constitution_sha256": constitution_sha, "contract_sha256": contract_sha,
                    "write_paths": paths})
                if (not isinstance(approval, dict) or approval.get("approved") is not True
                        or approval.get("writer") != "N4" or not approval.get("approval_ref")):
                    raise ContractError("BLOCKED_APPROVAL")
            claim = await _call(self.p.queue_claim, {"project_id": project_id,
                "loop_id": lid, "trigger_id": tid, "contract_sha256": contract_sha,
                "constitution_sha256": constitution_sha})
            if not isinstance(claim, dict) or claim.get("claimed") is not True or not claim.get("receipt_ref"):
                raise ContractError("QUEUE_NOT_CONNECTED")
            current.update(status="STARTED", claim_ref=claim["receipt_ref"], anchor_receipts=refs)
            # The claim already took effect in CIT-50. If the durable
            # STARTED checkpoint fails, report reconciliation instead of
            # pretending no execution was claimed.
            started = True
            await self._save(key, current)
            model_data, model_evidence, tool_receipts, read_observations = {}, [], [], []
            for step in ordered_steps(contract):
                if step["kind"] == "MODEL":
                    prompt = {"task_id": tid, "input_block_verbatim": contract["input_block_verbatim"],
                        "steps": contract["steps"], "category": contract["category"],
                        "source_sha256": contract["source"]["sha256"], "anchor_receipts": refs,
                        "note_is_untrusted_metadata": contract.get("note", ""),
                        "scope": contract["execution"]["write_paths"],
                        "anchored_source_bytes_decoded": source_context,
                        "verified_read_observations": read_observations}
                    result = await asyncio.wait_for(_call(self.p.model, selection, prompt),
                              timeout=contract["execution"].get("timeout_s", 120))
                    if not isinstance(result, dict) or result.get("finish_reason") != "stop":
                        raise ContractError("PARTIAL_MODEL_OUTPUT")
                    if result.get("status") != "READY" or not isinstance(result.get("data"), dict):
                        raise ContractError("MODEL_RESULT_INVALID")
                    model_data = result["data"]
                    model_evidence = result.get("evidence_refs", [])
                    if not isinstance(model_evidence, list) or any(not isinstance(e, str) for e in model_evidence):
                        raise ContractError("MODEL_EVIDENCE_INVALID")
                elif step["kind"] == "TOOL":
                    op, args = step["tool"], dict(step.get("args", {}))
                    if "text_from_model" in args:
                        field = args.pop("text_from_model")
                        if not isinstance(field, str) or not isinstance(model_data.get(field), str):
                            raise ContractError("MODEL_TEXT_MISSING")
                        args["text"] = model_data[field]
                    if op in WRITE_OPS:
                        mutating = True
                        current["mutating_step"] = {"step_id": step["id"], "op": op,
                            "path": args.get("path"), "fingerprint": sha256(canonical({
                              "trigger_id": tid, "step_id": step["id"],
                              "constitution": constitution_sha, "tool": op, "args": args}))}
                        await self._save(key, current)
                    tool_result = await _call(self.p.tool, op, args, {"project_id": project_id,
                        "loop_id": lid, "trigger_id": tid, "authorization": approval,
                        "claim_ref": claim["receipt_ref"], "constitution_sha256": constitution_sha})
                    if (not isinstance(tool_result, dict) or tool_result.get("ok") is not True
                            or not tool_result.get("evidence_ref")):
                        raise ContractError("TOOL_EVIDENCE_MISSING", op)
                    receipt = {"step_id": step["id"], "op": op, "evidence_ref": tool_result["evidence_ref"]}
                    if op in READ_OPS:
                        observation = {"step_id": step["id"], "op": op, "source": args, "result": tool_result}
                        if len(canonical(observation)) > 100_000:
                            raise ContractError("SOURCE_TOO_LARGE_NEEDS_SEGMENT")
                        read_observations.append(observation)
                    if op in WRITE_OPS:
                        check_op = "read_text" if op == "write_text" else "verify_exists"
                        verified = await _call(self.p.tool, check_op, {"path": args["path"]},
                            {"project_id": project_id, "loop_id": lid, "trigger_id": tid,
                             "authorization": None, "constitution_sha256": constitution_sha})
                        if (not isinstance(verified, dict) or verified.get("ok") is not True
                             or not verified.get("evidence_ref")
                             or (check_op == "read_text" and verified.get("text") != args.get("text"))):
                            raise ContractError("READBACK_MISMATCH")
                        receipt["readback_ref"] = verified["evidence_ref"]
                    tool_receipts.append(receipt)
                    current["receipts"] = list(tool_receipts)
                    await self._save(key, current)
            outputs = contract["outputs"]
            if any(k not in model_data for k in outputs["required_fields"]):
                raise ContractError("OUTPUT_CONTRACT_FAILED")
            if outputs["require_tool_receipt"] and not tool_receipts:
                raise ContractError("PASS_SIN_EVIDENCIA")
            if outputs["require_readback"] and any(r.get("op") in WRITE_OPS and not r.get("readback_ref") for r in tool_receipts):
                raise ContractError("READBACK_REQUIRED")
            if not any(r.get("op") in (READ_OPS | WRITE_OPS) for r in tool_receipts) and not refs:
                raise ContractError("PASS_SIN_EVIDENCIA")
            constitutional_after, _ = await self._constitution()
            if constitutional_after != constitution_sha:
                raise ContractError("CONSTITUTION_CHANGED_DURING_TASK")
            for ref, old in refs.items():
                fresh = await _call(self.p.anchor, ref)
                if not isinstance(fresh, dict) or fresh.get("sha256") != old["sha256"] or sha256(fresh.get("bytes", b"")) != old["sha256"]:
                    raise ContractError("SOURCE_CHANGED_DURING_TASK")
            if self.p.queue_complete is not None:
                qreceipt = await _call(self.p.queue_complete, claim["receipt_ref"], {
                    "verification": "PASS", "trigger_id": tid,
                    "contract_sha256": contract_sha, "tool_receipts": tool_receipts,
                    "source_sha256": contract["source"]["sha256"]})
                if not isinstance(qreceipt, dict) or qreceipt.get("ok") is not True or not qreceipt.get("evidence_ref"):
                    raise ContractError("QUEUE_COMPLETION_FAILED")
                current["queue_receipt_ref"] = qreceipt["evidence_ref"]
            current.update(ok=True, status="PASS", data=model_data,
                model_evidence_refs=model_evidence, receipts=tool_receipts,
                flags=[], next="NEXT")
            await self._save(key, current)
            return current
        except asyncio.TimeoutError:
            return await self._failed(key, current, "MODEL_TIMEOUT", started, mutating)
        except ContractError as e:
            return await self._failed(key, current, e.code, started, mutating or e.code == "NEEDS_RECONCILIATION")
        except (OSError, RuntimeError, ValueError, TypeError, KeyError):
            return await self._failed(key, current, "HOST_PORT_FAILURE", started, mutating)
