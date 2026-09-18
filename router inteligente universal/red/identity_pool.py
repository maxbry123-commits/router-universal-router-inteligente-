"""Fail-closed provider/API identity pool for RedUniversal.

This module does not route messages and never stores secret values.
It selects one eligible identity at a time; RedUniversal remains the routing owner.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class IdentitySpec:
    identity_id: str
    provider: str
    connector_kind: str
    secret_env: str
    priority: int = 100
    logical_model_id: str = ""
    repo_id: str = ""
    endpoint_ref: str = ""
    mirror_rank: int = 0

    def __post_init__(self) -> None:
        if not self.identity_id.strip():
            raise ValueError("identity_id_obligatorio")
        if not self.provider.strip():
            raise ValueError("provider_obligatorio")
        if not self.connector_kind.strip():
            raise ValueError("connector_kind_obligatorio")
        if not self.secret_env.strip():
            raise ValueError("secret_env_obligatorio")
        if self.mirror_rank < 0:
            raise ValueError("mirror_rank_invalido")


@dataclass
class IdentityState:
    enabled: bool = True
    quota_exhausted: bool = False
    cooldown_until: float = 0.0
    failures: int = 0

    def eligible(self, now: float) -> bool:
        return self.enabled and not self.quota_exhausted and now >= self.cooldown_until


class IdentityPool:
    """Data-driven pool supporting arbitrary identity counts without fan-out."""

    def __init__(self) -> None:
        self._specs: dict[str, IdentitySpec] = {}
        self._state: dict[str, IdentityState] = {}

    @staticmethod
    def _validate_connector_kind(kind: str) -> None:
        # Late import avoids making connector dependencies part of module import.
        from red.connector_registry import CONNECTOR_REGISTRY
        if kind not in CONNECTOR_REGISTRY:
            raise ValueError(f"conector_no_registrado:{kind}")

    def register(self, spec: IdentitySpec) -> None:
        self.register_many([spec])

    def register_many(self, specs: Iterable[IdentitySpec]) -> None:
        batch = list(specs)
        ids = [spec.identity_id for spec in batch]
        if len(ids) != len(set(ids)):
            raise ValueError("identidad_duplicada_en_batch")
        if any(identity_id in self._specs for identity_id in ids):
            raise ValueError("identidad_duplicada_existente")
        for spec in batch:
            self._validate_connector_kind(spec.connector_kind)
        # Mutate only after the full batch validates.
        for spec in batch:
            self._specs[spec.identity_id] = spec
            self._state[spec.identity_id] = IdentityState()

    def select(
        self,
        *,
        provider: str,
        now: float,
        logical_model_id: str = "",
    ) -> IdentitySpec | None:
        candidates: list[IdentitySpec] = []
        for identity_id, spec in self._specs.items():
            state = self._state[identity_id]
            if spec.provider != provider or not state.eligible(now):
                continue
            if logical_model_id and spec.logical_model_id != logical_model_id:
                continue
            candidates.append(spec)
        candidates.sort(
            key=lambda spec: (
                spec.priority,
                spec.mirror_rank,
                spec.identity_id,
            )
        )
        return candidates[0] if candidates else None

    def mark_quota_exhausted(self, identity_id: str) -> None:
        self._require(identity_id).quota_exhausted = True

    def mark_cooldown(self, identity_id: str, until: float) -> None:
        state = self._require(identity_id)
        state.cooldown_until = max(state.cooldown_until, float(until))

    def mark_failure(self, identity_id: str) -> None:
        self._require(identity_id).failures += 1

    def restore(self, identity_id: str) -> None:
        state = self._require(identity_id)
        state.enabled = True
        state.quota_exhausted = False
        state.cooldown_until = 0.0
        state.failures = 0

    def disable(self, identity_id: str) -> None:
        self._require(identity_id).enabled = False

    def _require(self, identity_id: str) -> IdentityState:
        try:
            return self._state[identity_id]
        except KeyError as exc:
            raise ValueError(f"identidad_no_registrada:{identity_id}") from exc

    def count(self) -> int:
        return len(self._specs)

    def snapshot(self) -> dict:
        """Safe metadata snapshot: secret references only, never secret values."""
        return {
            identity_id: {
                "provider": spec.provider,
                "connector_kind": spec.connector_kind,
                "secret_env": spec.secret_env,
                "priority": spec.priority,
                "logical_model_id": spec.logical_model_id,
                "repo_id": spec.repo_id,
                "endpoint_ref": spec.endpoint_ref,
                "mirror_rank": spec.mirror_rank,
                "enabled": self._state[identity_id].enabled,
                "quota_exhausted": self._state[identity_id].quota_exhausted,
                "cooldown_until": self._state[identity_id].cooldown_until,
                "failures": self._state[identity_id].failures,
            }
            for identity_id, spec in sorted(self._specs.items())
        }
