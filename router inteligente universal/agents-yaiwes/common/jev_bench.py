"""Benchmarks Laya Multilingual (322M), Decider-0.8B and Decider-2B on the 8 real router decisions the Director's research proposed,
on a plain CPU runner (no GPU, no HF billing). Measures accuracy against the expected label, latency and whether the pip packages even
install — real results only, a failed install is reported as a failure, never faked.
"""
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
    try:
        from decider.infer import Decider  # type: ignore
    except Exception as exc:  # noqa: BLE001
        note(model_id.upper().replace("/", "_").replace(".", "_") + "_INSTALL", f"NO DISPONIBLE: {type(exc).__name__}: {exc}", "warning")
        return
    try:
        d = Decider(model_id)
    except Exception as exc:  # noqa: BLE001
        note(model_id.upper().replace("/", "_").replace(".", "_") + "_LOAD", f"NO CARGÓ: {type(exc).__name__}: {exc}", "warning")
        return
    hits, lat = 0, []
    for state, expected in CASES:
        t0 = time.perf_counter()
        try:
            result = d.system_one(state, QUESTIONS)
            route = (result.get("route") or {}).get("choice") if isinstance(result, dict) else None
        except Exception as exc:  # noqa: BLE001
            note(model_id.upper().replace("/", "_").replace(".", "_") + "_CASE_ERROR", f"{state['task'][:40]}: {type(exc).__name__}", "warning")
            continue
        lat.append((time.perf_counter() - t0) * 1000)
        hits += int(route == expected)
    if lat:
        note(model_id.upper().replace("/", "_").replace(".", "_"), f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


def bench_laya(model_id: str) -> None:
    try:
        import laya  # type: ignore
    except Exception as exc:  # noqa: BLE001
        note("LAYA_INSTALL", f"NO DISPONIBLE: {type(exc).__name__}: {exc}", "warning")
        return
    try:
        agent = laya.load(model_id)
    except Exception as exc:  # noqa: BLE001
        note("LAYA_LOAD", f"NO CARGÓ: {type(exc).__name__}: {exc}", "warning")
        return
    hits, lat = 0, []
    for state, expected in CASES:
        t0 = time.perf_counter()
        try:
            result = agent.predict(state, QUESTIONS)
            route = (result.get("route") or {}).get("choice") if isinstance(result, dict) else None
        except Exception as exc:  # noqa: BLE001
            note("LAYA_CASE_ERROR", f"{state['task'][:40]}: {type(exc).__name__}", "warning")
            continue
        lat.append((time.perf_counter() - t0) * 1000)
        hits += int(route == expected)
    if lat:
        note("LAYA_MULTILINGUAL", f"aciertos={hits}/{len(CASES)} latencia_media_ms={sum(lat) / len(lat):.1f}")


def main() -> int:
    bench_laya("convaiinnovations/laya-multilingual")
    bench_decider("Mapika/decider-0.8b")
    bench_decider("Mapika/decider-2b")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        note("ERROR_GENERAL", traceback.format_exc()[-400:], "warning")
        raise SystemExit(1)
