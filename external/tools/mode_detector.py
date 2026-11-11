"""
mode_detector.py — Deteccion de modo en 3 tiers (heuristica -> embedding -> clasificador)
Ubicacion: external/tools/mode_detector.py
Regla: detenerse en el primer tier con confianza > 0.8. Determinista.
Fallback: si sentence-transformers no esta instalado, tier1 devuelve confianza 0.
"""
from __future__ import annotations
import json
import re
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "registry_modos.json"

KEYWORDS: Dict[str, list] = {
    "code_generate": ["write", "implement", "create a function", "escribir", "implementar"],
    "code_refactor": ["refactor", "clean up", "restructure", "refactorizar"],
    "code_debug": ["fix", "debug", "error", "stack trace", "arreglar", "depurar"],
    "code_review": ["review", "critique", "what's wrong", "revisar"],
    "architecture": ["design", "architect", "system design", "tradeoffs", "arquitectura"],
    "reasoning": ["prove", "analyze", "why", "deduce", "razonar", "analizar"],
    "planning": ["plan", "roadmap", "steps", "checklist", "planificar"],
    "documentation": ["document", "explain", "boilerplate", "documentar"],
    "creative": ["write a story", "generate", "creative", "imagine", "creativo"],
    "summarize": ["summarize", "summary", "resumir"],
    "translate": ["translate", "traducir"],
    "chat": ["hello", "hi", "hola", "como estas"],
}

TOOL_CALL_PATTERN = re.compile(r'"tools"\s*:\s*\[', re.IGNORECASE)


def _load_registry() -> Dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"modes": {}}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def tier0_heuristics(prompt: str, has_tools: bool) -> Tuple[str, float]:
    if has_tools or TOOL_CALL_PATTERN.search(prompt):
        return "tool_call", 0.95
    low = prompt.lower()
    for mode, words in KEYWORDS.items():
        if any(w in low for w in words):
            return mode, 0.85
    if len(prompt.split()) < 20:
        return "quick_fact", 0.80
    return "unknown", 0.0


def tier1_embeddings(prompt: str) -> Tuple[str, float]:
    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore
    except Exception:
        logger.debug("sentence-transformers no disponible; tier1 omitido")
        return "unknown", 0.0
    reg = _load_registry().get("modes", {})
    if not reg:
        return "unknown", 0.0
    model = SentenceTransformer("all-MiniLM-L6-v2")
    emb = model.encode(prompt)
    scores: Dict[str, float] = {}
    for mode, meta in reg.items():
        seed = meta.get("seed", mode)
        cent = model.encode(seed)
        scores[mode] = float(util.cos_sim(emb, cent)[0][0])
    best = max(scores, key=scores.get)
    return best, scores[best]


def tier2_classifier(prompt: str) -> Tuple[str, float]:
    # Stub determinista: sin modelo clasificador local, devuelve reasoning con 0.0
    # y flag para que el orquestador decida. No inventa salida.
    logger.warning("tier2 sin clasificador local; devuelve unknown con flag")
    return "unknown", 0.0


def detect_mode(prompt: str, has_tools: bool = False) -> Dict[str, Any]:
    mode, conf = tier0_heuristics(prompt, has_tools)
    if conf > 0.8:
        return {"mode": mode, "confidence": conf, "tier": 0}
    mode, conf = tier1_embeddings(prompt)
    if conf > 0.8:
        return {"mode": mode, "confidence": conf, "tier": 1}
    mode, conf = tier2_classifier(prompt)
    return {"mode": mode, "confidence": conf, "tier": 2, "flag": "needs_human_route"}


def resolve_lora(mode: str) -> Optional[Tuple[str, str]]:
    reg = _load_registry().get("modes", {})
    meta = reg.get(mode)
    if not meta:
        return None
    return (meta.get("dataset"), meta.get("lora_path"))
