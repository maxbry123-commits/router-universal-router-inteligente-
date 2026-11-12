"""
mode_router.py — 12 modos a (dataset, LoRA) (Control Plane)
"""
from __future__ import annotations
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ModeRouter:
    MODES = {
        "code_gen": ("swe-code-dataset", "lora-code-gen"),
        "code_review": ("swe-code-dataset", "lora-code-review"),
        "debug": ("swe-code-dataset", "lora-debug"),
        "test_gen": ("swe-code-dataset", "lora-test-gen"),
        "doc_gen": ("doc-dataset", "lora-doc-gen"),
        "refactor": ("swe-code-dataset", "lora-refactor"),
        "security_audit": ("security-dataset", "lora-security"),
        "performance": ("perf-dataset", "lora-perf"),
        "translate": ("i18n-dataset", "lora-translate"),
        "summarize": ("sum-dataset", "lora-sum"),
        "explain": ("explain-dataset", "lora-explain"),
        "chat": ("chat-dataset", "lora-chat"),
    }

    def __init__(self) -> None:
        self._registry: Dict[str, Tuple[str, str]] = self.MODES.copy()

    def select(self, mode: str) -> Optional[Tuple[str, str]]:
        result = self._registry.get(mode.lower().strip())
        if not result:
            logger.warning("Modo desconocido: %s", mode)
        return result

    def register_mode(self, mode: str, dataset: str, lora: str) -> None:
        self._registry[mode.lower().strip()] = (dataset, lora)

    def list_modes(self) -> list:
        return sorted(self._registry.keys())

    def validate_mode(self, mode: str) -> bool:
        return mode.lower().strip() in self._registry
