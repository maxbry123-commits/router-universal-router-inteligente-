"""24-case benchmark (the Director's package: R01-R04 routing, W01-W04 web-search-needed, C01-C04 cache, L01-L04 retry/loop,
B01-B04 budget, D01-D04 next-DAG-node) for the Jev-style decision models (Qwen3-0.6B-RLCD, Laya, Laya-typed-decisions, Decider-0.8B/2B)
AND for 3 general small LLMs used as decision-makers by prompting (HRM-Text-1B, LFM2.5-1.2B-Instruct, Qwen3-0.6B plain instruct).
Real results only, CPU-only, no GPU, no HF billing."""
from __future__ import annotations

import json
import re
import time
import traceback

CASES = [
    ("R01", {"task": "Return the current value of a known JSON field.", "data_available": True, "external_information_needed": False, "reasoning_complexity": "none"},
     "choice", ["RULE", "TOOL", "SMALL_LLM", "DEEPSEEK"], "RULE"),
    ("R02", {"task": "Run the existing unit test suite.", "tool_available": "test_runner", "reasoning_complexity": "none"},
     "choice", ["RULE", "TOOL", "SMALL_LLM", "DEEPSEEK"], "TOOL"),
    ("R03", {"task": "Classify an error message into network, syntax, or authentication.", "tool_available": False, "reasoning_complexity": "low"},
     "choice", ["RULE", "TOOL", "SMALL_LLM", "DEEPSEEK"], "SMALL_LLM"),
    ("R04", {"task": "Design a new distributed architecture with conflicting constraints.", "reasoning_complexity": "high", "multiple_tradeoffs": True},
     "choice", ["RULE", "TOOL", "SMALL_LLM", "DEEPSEEK"], "DEEPSEEK"),
    ("W01", {"question": "What is 2 + 2?", "knowledge_required": "none"}, "noul", None, False),
    ("W02", {"question": "What is the current API price of a provider?", "information_changes_over_time": True}, "noul", None, True),
    ("W03", {"question": "Read the error from the provided local log.", "log_present": True, "external_information_needed": False}, "noul", None, False),
    ("W04", {"question": "Find the newest stable release of this library.", "current_version_unknown": True}, "noul", None, True),
    ("C01", {"task_hash": "abc123", "cached_hash": "abc123", "cache_valid": True}, "noul", None, False),
    ("C02", {"task_hash": "abc124", "cached_hash": "abc123", "cache_valid": True}, "noul", None, True),
    ("C03", {"dependency_changed": False, "previous_result_valid": True}, "noul", None, False),
    ("C04", {"dependency_changed": True, "previous_result_valid": True}, "noul", None, True),
    ("L01", {"attempts": 0, "max_attempts": 2, "last_attempt_failed": True, "progress_detected": True}, "noul", None, True),
    ("L02", {"attempts": 2, "max_attempts": 2, "last_attempt_failed": True}, "noul", None, False),
    ("L03", {"attempts": 3, "same_error_repeated": 3, "progress_detected": False}, "noul", None, False),
    ("L04", {"attempts": 1, "new_information_found": True, "progress_detected": True}, "noul", None, True),
    ("B01", {"remaining_budget_usd": 0.001, "estimated_next_call_usd": 0.01}, "noul", None, False),
    ("B02", {"remaining_budget_usd": 0.05, "estimated_next_call_usd": 0.01, "task_requires_reasoning": True}, "noul", None, True),
    ("B03", {"small_model_confidence": 0.96, "confidence_threshold": 0.85}, "noul", None, False),
    ("B04", {"small_model_confidence": 0.42, "confidence_threshold": 0.85}, "noul", None, True),
    ("D01", {"code_generated": True, "tests_run": False}, "choice", ["SEARCH", "GENERATE_CODE", "RUN_TESTS", "FINISH"], "RUN_TESTS"),
    ("D02", {"tests_run": True, "tests_passed": True, "requirements_met": True}, "choice", ["SEARCH", "GENERATE_CODE", "RUN_TESTS", "FINISH"], "FINISH"),
    ("D03", {"tests_run": True, "tests_passed": False, "error_understood": True}, "choice", ["SEARCH", "GENERATE_CODE", "PATCH_CODE", "FINISH"], "PATCH_CODE"),
    ("D04", {"tests_run": True, "tests_passed": False, "error_understood": False, "documentation_missing": True}, "choice", ["SEARCH", "PATCH_CODE", "RUN_TESTS", "FINISH"], "SEARCH"),
]
QUESTION_TEXT = {"R": "Which executor should handle this task?", "D": "What should happen next?", "W": "Is web research required?",
                 "C1": "Should this task be executed again?", "C2": "Should this DAG node run?", "L1": "Should the agent retry?",
                 "L2": "Should execution continue?", "B1": "Should the expensive model be called?", "B2": "Should the request escalate to a larger model?"}


def note(title: str, msg: str, level: str = "notice") -> None:
    print(f"::{level} title=RIU_BENCH24_{title}::{msg}".replace("\n", " ")[:900], flush=True)


def question_for(case_id: str) -> str:
    if case_id.startswith(("R",)):
        return QUESTION_TEXT["R"]
    if case_id.startswith("D"):
        return QUESTION_TEXT["D"]
    if case_id.startswith("W"):
        return QUESTION_TEXT["W"]
    if case_id in ("C01", "C02"):
        return QUESTION_TEXT["C1"]
    if case_id in ("C03", "C04"):
        return QUESTION_TEXT["C2"]
    if case_id in ("L01", "L02"):
        return QUESTION_TEXT["L1"]
    if case_id in ("L03", "L04"):
        return QUESTION_TEXT["L2"]
    if case_id in ("B01", "B02"):
        return QUESTION_TEXT["B1"]
    return QUESTION_TEXT["B2"]


def score(predict_fn) -> tuple[int, list[float]]:
    hits, lat = 0, []
    for cid, state, qtype, options, expected in CASES:
        t0 = time.perf_counter()
        try:
            ans = predict_fn(state, question_for(cid), qtype, options)
        except Exception as exc:  # noqa: BLE001
            note(f"CASE_ERROR_{cid}", f"{type(exc).__name__}: {str(exc)[:100]}", "warning")
            continue
        lat.append((time.perf_counter() - t0) * 1000)
        ok = (ans == expected) if qtype == "choice" else (bool(ans) == expected)
        hits += int(ok)
    return hits, lat


# ---- Jev-style decision models -----------------------------------------------------------------
def bench_decider(model_id: str) -> None:
    tag = model_id.upper().replace("/", "_").replace(".", "_").replace("-", "_")
    try:
        from decider.infer import Decider  # type: ignore
        d = Decider(model_id)
    except Exception as exc:  # noqa: BLE001
        note(tag + "_UNAVAILABLE", f"{type(exc).__name__}: {str(exc)[:150]}", "warning")
        return

    def predict(state, qtext, qtype, options):
        qs = {"q": {"type": {"choice": "choice", "noul": "noul"}[qtype], "instructions": qtext}}
        if options:
            qs["q"]["criteria"] = {o: o for o in options}
        out = d.system_one(state, qs)
        return out.get("q", {}).get("choice") if qtype == "choice" else out.get("q", {}).get("noul", 0) > 0.5

    hits, lat = score(predict)
    if lat:
        note(tag, f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


def bench_laya(model_id: str, subfolder: str | None, label: str) -> None:
    try:
        import laya  # type: ignore
        agent = laya.load(model_id, subfolder=subfolder) if subfolder else laya.load(model_id)
    except Exception as exc:  # noqa: BLE001
        note(f"LAYA_{label}_UNAVAILABLE", f"{type(exc).__name__}: {str(exc)[:150]}", "warning")
        return

    def predict(state, qtext, qtype, options):
        qs = {"q": {"type": qtype, "instructions": qtext}}
        if options:
            qs["q"]["criteria"] = {o: o for o in options}
        out = agent.predict(state, qs)
        a = (out.get("answers") or {}).get("q", {})
        return a.get("choice") if qtype == "choice" else a.get("noul", 0) > 0.5

    hits, lat = score(predict)
    if lat:
        note(f"LAYA_{label}", f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


# ---- generic small LLMs, used by PROMPTING (not a dedicated decision head) --------------------
def bench_generic_llm(model_id: str, tag: str, max_new_tokens: int = 40) -> None:
    try:
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
        tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32, trust_remote_code=True)
    except Exception as exc:  # noqa: BLE001
        note(f"{tag}_UNAVAILABLE", f"{type(exc).__name__}: {str(exc)[:150]}", "warning")
        return

    def predict(state, qtext, qtype, options):
        if qtype == "choice":
            prompt = f"State: {json.dumps(state)}\nQuestion: {qtext}\nOptions: {', '.join(options)}\nAnswer with exactly one option, nothing else.\nAnswer:"
        else:
            prompt = f"State: {json.dumps(state)}\nQuestion: {qtext}\nAnswer with exactly true or false, nothing else.\nAnswer:"
        ids = tok(prompt, return_tensors="pt")
        out = model.generate(**ids, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id)
        text = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip().upper()
        if qtype == "choice":
            for o in options:
                if o in text:
                    return o
            return None
        return "TRUE" in text and "FALSE" not in text

    hits, lat = score(predict)
    if lat:
        note(tag, f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


def main() -> int:
    note("INFO", f"{len(CASES)} casos (paquete del Director: R,W,C,L,B,D)")
    bench_laya("convaiinnovations/laya", None, "ENGLISH_BASE")
    bench_laya("convaiinnovations/laya", "typed-decisions", "TYPED_DECISIONS_FINETUNED")
    bench_decider("Mapika/decider-0.8b")
    bench_decider("Mapika/decider-2b")
    bench_generic_llm("anthonym21/qwen3-0.6b-rlcd-decision", "QWEN_RLCD_DECISION")
    bench_generic_llm("Qwen/Qwen3-0.6B", "QWEN3_0_6B_PLAIN")
    bench_generic_llm("LiquidAI/LFM2.5-1.2B-Instruct", "LFM2_5_1_2B_INSTRUCT")
    bench_generic_llm("sapientinc/HRM-Text-1B", "HRM_TEXT_1B")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        note("ERROR_GENERAL", traceback.format_exc()[-400:], "warning")
        raise SystemExit(1)
