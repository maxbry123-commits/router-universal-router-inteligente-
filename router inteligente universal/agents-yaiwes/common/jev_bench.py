"""Benchmarks Laya (laya-typed-decisions, the fine-tuned checkpoint), Decider-0.8B/2B and Qwen3-0.6B-RLCD-Decision on the 8 real router
decisions the Director's research proposed, on a plain CPU runner (no GPU, no HF billing). Real results only.
FIX (2026-09-22): the previous run read result["route"]["choice"]; Laya's real key is result["answers"]["route"]["choice"]."""
from __future__ import annotations

import time
import traceback

CASES = [
    ({"task": "Cambiar valor conocido en JSON", "files": 1, "tests_failed": 0, "research_needed": False}, "rule"),
    ({"task": "Ejecutar tests existentes", "files": 0, "tests_failed": 0, "research_needed": False}, "tool"),
    ({"task": "Clasificar un error sencillo de configuración", "files": 2, "tests_failed": 1, "research_needed": False}, "small_llm"),
    ({"task": "Diseñar una arquitectura nueva de servicios", "files": 12, "tests_failed": 0, "research_needed": True}, "deepseek"),
    ({"task": "El resultado ya está en caché", "files": 0, "tests_failed": 0, "research_needed": False}, "rule"),
    ({"task": "Error desconocido después de 2 intentos fallidos", "files": 3, "tests_failed": 2, "research_needed": False}, "deepseek"),
    ({"task": "Los tests pasaron correctamente", "files": 1, "tests_failed": 0, "research_needed": False}, "finish"),
    ({"task": "Falta un dato verificable, hay que buscarlo en la web", "files": 0, "tests_failed": 0, "research_needed": True}, "research"),
]
QUESTIONS = {
    "route": {"type": "choice", "instructions": "¿Qué ejecutor debe resolver esta tarea?",
              "criteria": {"rule": "regla determinista", "tool": "una herramienta la resuelve", "small_llm": "interpretación sencilla",
                           "deepseek": "razonamiento complejo", "finish": "ya terminó", "research": "hace falta investigar"}},
}


def note(title: str, msg: str, level: str = "notice") -> None:
    print(f"::{level} title=RIU_JEVBENCH_{title}::{msg}".replace("\n", " ")[:900], flush=True)


def bench_decider(model_id: str) -> None:
    tag = model_id.upper().replace("/", "_").replace(".", "_").replace("-", "_")
    try:
        from decider.infer import Decider  # type: ignore
    except Exception as exc:  # noqa: BLE001
        note(tag + "_INSTALL", f"NO DISPONIBLE: {type(exc).__name__}: {exc}", "warning")
        return
    try:
        d = Decider(model_id)
    except Exception as exc:  # noqa: BLE001
        note(tag + "_LOAD", f"NO CARGÓ (confirmado por su README: está hecho para GH200/CUDA graphs, sin ruta de CPU): {type(exc).__name__}: {exc}", "warning")
        return
    hits, lat = 0, []
    for state, expected in CASES:
        t0 = time.perf_counter()
        try:
            result = d.system_one(state, QUESTIONS)
            route = (result.get("route") or {}).get("choice") if isinstance(result, dict) else None
        except Exception as exc:  # noqa: BLE001
            note(tag + "_CASE_ERROR", f"{state['task'][:40]}: {type(exc).__name__}", "warning")
            continue
        lat.append((time.perf_counter() - t0) * 1000)
        hits += int(route == expected)
    if lat:
        note(tag, f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


def bench_laya(model_id: str, subfolder: str | None, label: str) -> None:
    try:
        import laya  # type: ignore
    except Exception as exc:  # noqa: BLE001
        note("LAYA_INSTALL", f"NO DISPONIBLE: {type(exc).__name__}: {exc}", "warning")
        return
    try:
        agent = laya.load(model_id, subfolder=subfolder) if subfolder else laya.load(model_id)
    except Exception as exc:  # noqa: BLE001
        note(f"LAYA_{label}_LOAD", f"NO CARGÓ: {type(exc).__name__}: {exc}", "warning")
        return
    hits, lat = 0, []
    for state, expected in CASES:
        t0 = time.perf_counter()
        try:
            result = agent.predict(state, QUESTIONS)
            route = (result.get("answers") or {}).get("route", {}).get("choice") if isinstance(result, dict) else None
        except Exception as exc:  # noqa: BLE001
            note(f"LAYA_{label}_CASE_ERROR", f"{state['task'][:40]}: {type(exc).__name__}", "warning")
            continue
        lat.append((time.perf_counter() - t0) * 1000)
        hits += int(route == expected)
    if lat:
        note(f"LAYA_{label}", f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


def bench_qwen_rlcd(model_id: str) -> None:
    try:
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except Exception as exc:  # noqa: BLE001
        note("QWEN_RLCD_INSTALL", f"NO DISPONIBLE: {type(exc).__name__}: {exc}", "warning")
        return
    try:
        tok = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
    except Exception as exc:  # noqa: BLE001
        note("QWEN_RLCD_LOAD", f"NO CARGÓ en CPU: {type(exc).__name__}: {exc}", "warning")
        return
    hits, lat = 0, []
    letters, opts = "ABCDEF", list(QUESTIONS["route"]["criteria"])
    for state, expected in CASES:
        prompt = f"Context: {state}\nQuestion: {QUESTIONS['route']['instructions']}\n" + "\n".join(f"{letters[i]}. {o}" for i, o in enumerate(opts)) + "\nAnswer: ("
        t0 = time.perf_counter()
        try:
            ids = tok(prompt, return_tensors="pt")
            with torch.no_grad():
                logits = model(**ids).logits[0, -1]
            opt_ids = [tok(letters[i], add_special_tokens=False).input_ids[0] for i in range(len(opts))]
            choice = opts[int(torch.tensor([logits[i] for i in opt_ids]).argmax())]
        except Exception as exc:  # noqa: BLE001
            note("QWEN_RLCD_CASE_ERROR", f"{state['task'][:40]}: {type(exc).__name__}", "warning")
            continue
        lat.append((time.perf_counter() - t0) * 1000)
        hits += int(choice == expected)
    if lat:
        note("QWEN3_0_6B_RLCD_DECISION", f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


def main() -> int:
    bench_laya("convaiinnovations/laya", None, "ENGLISH_BASE")
    bench_laya("convaiinnovations/laya", "typed-decisions", "TYPED_DECISIONS_FINETUNED")
    bench_decider("Mapika/decider-0.8b")
    bench_decider("Mapika/decider-2b")
    bench_qwen_rlcd("anthonym21/qwen3-0.6b-rlcd-decision")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        note("ERROR_GENERAL", traceback.format_exc()[-400:], "warning")
        raise SystemExit(1)
