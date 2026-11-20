"""env_config.py — Mapeo tipado de env-vars del proxy (P1-6).
- Fail-soft: valores ausentes → default/None con warning.
- NUNCA loguea valores completos (solo prefijo + len).
- Snapshot inmutable al primer get_env().
"""
import os
import logging

logger = logging.getLogger(__name__)


def _get(name: str, default=None, required: bool = False) -> str | None:
    v = os.getenv(name)
    if v is None or v == "":
        if required:
            logger.warning(f"[env] MISSING required: {name}")
        return default
    return v


def _mask(v: str | None) -> str:
    if not v:
        return "<empty>"
    return f"{v[:4]}***({len(v)})"


class EnvConfig:
    def __init__(self):
        self.ROUTER_API_KEY    = _get("ROUTER_API_KEY", required=True)
        self.HF_TOKEN          = _get("HF_TOKEN")
        self.GITHUB_TOKEN      = _get("GITHUB_TOKEN")
        self.HARNESS_KEY       = _get("HARNESS_KEY") or self.ROUTER_API_KEY
        self.AGENT_HARNESS_URL = _get("AGENT_HARNESS_URL")
        self.HF_VAULT_KEY      = _get("HF_VAULT_KEY")
        self.CHECKPOINT_DIR    = _get("CHECKPOINT_DIR", "state/checkpoints")
        self.LOOP_MAX_ITER     = int(_get("LOOP_MAX_ITER", "8"))
        self.CONTEXT7_API_KEY  = _get("CONTEXT7_API_KEY")
        self.FIRECRAWL_API_KEY = _get("FIRECRAWL_API_KEY")

    def masked_summary(self) -> dict:
        return {
            "ROUTER_API_KEY":    _mask(self.ROUTER_API_KEY),
            "HF_TOKEN":          _mask(self.HF_TOKEN),
            "GITHUB_TOKEN":      _mask(self.GITHUB_TOKEN),
            "HARNESS_KEY":       _mask(self.HARNESS_KEY),
            "AGENT_HARNESS_URL": self.AGENT_HARNESS_URL or "<unset>",
            "HF_VAULT_KEY":      _mask(self.HF_VAULT_KEY),
            "CHECKPOINT_DIR":    self.CHECKPOINT_DIR,
            "LOOP_MAX_ITER":     self.LOOP_MAX_ITER,
        }

    def validate_required(self) -> list:
        missing = []
        if not self.ROUTER_API_KEY:
            missing.append("ROUTER_API_KEY")
        if not self.AGENT_HARNESS_URL:
            missing.append("AGENT_HARNESS_URL")
        if not self.HARNESS_KEY:
            missing.append("HARNESS_KEY")
        return missing


_cfg: EnvConfig | None = None


def get_env() -> EnvConfig:
    global _cfg
    if _cfg is None:
        _cfg = EnvConfig()
        miss = _cfg.validate_required()
        if miss:
            logger.warning(f"[env] faltan requeridas: {miss}")
    return _cfg
