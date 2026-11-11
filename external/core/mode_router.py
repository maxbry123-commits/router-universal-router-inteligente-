"""mode_router.py — Cablea mode_detector al proxy
NOTA: DISTINTO a router_llm_hf/mode_router.py (commit 48ab8f6d ya en rama).
"""
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    from external.tools.mode_detector import detect_mode, resolve_lora
except ImportError:
    try:
        from tools.mode_detector import detect_mode, resolve_lora
    except ImportError:
        def detect_mode(prompt, has_tools=False):
            return {"mode": "unknown", "confidence": 0.0, "tier": -1}
        def resolve_lora(mode):
            return None


def route(prompt: str, has_tools: bool = False) -> Dict[str, Any]:
    det = detect_mode(prompt, has_tools)
    lora = resolve_lora(det.get("mode", ""))
    return {"detection": det, "lora": lora, "mode": det.get("mode", "unknown")}


def select_model_for_mode(mode: str) -> Optional[Tuple[str, str]]:
    return resolve_lora(mode)
