from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from red.identity_pool import IdentityPool, IdentitySpec  # noqa: E402


def spec(i: int, **kw) -> IdentitySpec:
    return IdentitySpec(
        identity_id=f"hf-{i:02d}",
        provider=kw.pop("provider", "huggingface"),
        connector_kind=kw.pop("connector_kind", "huggingface"),
        secret_env=kw.pop("secret_env", f"HF_TOKEN_{i:02d}"),
        priority=kw.pop("priority", i),
        logical_model_id=kw.pop("logical_model_id", "code"),
        repo_id=kw.pop("repo_id", "unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF"),
        endpoint_ref=kw.pop("endpoint_ref", f"endpoint-{i:02d}"),
        mirror_rank=kw.pop("mirror_rank", 0),
        **kw,
    )


def test_registers_and_rolls_over_64_identities_sequentially() -> None:
    pool = IdentityPool()
    pool.register_many(spec(i) for i in range(64))
    assert pool.count() == 64

    selected = []
    for _ in range(64):
        current = pool.select(provider="huggingface", logical_model_id="code", now=0)
        assert current is not None
        selected.append(current.identity_id)
        pool.mark_quota_exhausted(current.identity_id)

    assert selected == [f"hf-{i:02d}" for i in range(64)]
    assert pool.select(provider="huggingface", logical_model_id="code", now=0) is None


def test_priority_mirror_and_cooldown_are_deterministic() -> None:
    pool = IdentityPool()
    pool.register_many([
        spec(1, priority=10, mirror_rank=1),
        spec(2, priority=10, mirror_rank=0),
        spec(3, priority=20, mirror_rank=0),
    ])
    assert pool.select(provider="huggingface", now=0).identity_id == "hf-02"
    pool.mark_cooldown("hf-02", until=100)
    assert pool.select(provider="huggingface", now=50).identity_id == "hf-01"
    assert pool.select(provider="huggingface", now=100).identity_id == "hf-02"


def test_batch_registration_is_atomic_and_connector_kind_is_validated() -> None:
    pool = IdentityPool()
    with pytest.raises(ValueError, match="conector_no_registrado"):
        pool.register_many([spec(0), spec(1, connector_kind="does-not-exist")])
    assert pool.count() == 0

    with pytest.raises(ValueError, match="identidad_duplicada_en_batch"):
        pool.register_many([spec(0), spec(0)])
    assert pool.count() == 0


def test_snapshot_contains_secret_refs_not_secret_values() -> None:
    pool = IdentityPool()
    pool.register(spec(0, secret_env="HF_TOKEN_ACCOUNT_00"))
    snap = pool.snapshot()["hf-00"]
    assert snap["secret_env"] == "HF_TOKEN_ACCOUNT_00"
    assert "token" not in {k.lower() for k in snap if k != "secret_env"}


def test_unknown_identity_fails_closed() -> None:
    pool = IdentityPool()
    with pytest.raises(ValueError, match="identidad_no_registrada"):
        pool.disable("missing")
