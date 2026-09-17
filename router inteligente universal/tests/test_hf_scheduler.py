from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integration.huggingface.hf_scheduler import (  # noqa: E402
    HFSlot,
    RAM_THRESHOLD,
    choose_hf_slot,
    scheduler_decision,
)


def test_prefers_hf1_then_hf2_then_hf3() -> None:
    assert choose_hf_slot([
        HFSlot("HF1", ram_percent=10),
        HFSlot("HF2", ram_percent=10),
        HFSlot("HF3", ram_percent=10),
    ]) == "HF1"
    assert choose_hf_slot([
        HFSlot("HF1", ram_percent=10, busy=True),
        HFSlot("HF2", ram_percent=20),
        HFSlot("HF3", ram_percent=10),
    ]) == "HF2"
    assert choose_hf_slot([
        HFSlot("HF1", ram_percent=RAM_THRESHOLD),
        HFSlot("HF2", ram_percent=99),
        HFSlot("HF3", ram_percent=30),
    ]) == "HF3"


def test_all_unavailable_waits() -> None:
    slots = [
        HFSlot("HF1", ram_percent=95),
        HFSlot("HF2", ram_percent=99),
        HFSlot("HF3", ram_percent=1, busy=True),
    ]
    assert scheduler_decision(slots) == {"state": "WAITING", "worker": None}


def test_missing_telemetry_fails_closed_instead_of_assuming_free() -> None:
    assert choose_hf_slot([]) is None
    assert choose_hf_slot([HFSlot("HF2", ram_percent=10)]) == "HF2"


def test_unknown_duplicate_and_invalid_ram_are_rejected() -> None:
    with pytest.raises(ValueError, match="UNKNOWN_HF_WORKER"):
        HFSlot("HF4", ram_percent=10)
    with pytest.raises(ValueError, match="HF_RAM_PERCENT_OUT_OF_RANGE"):
        HFSlot("HF1", ram_percent=101)
    with pytest.raises(ValueError, match="DUPLICATE_HF_WORKER"):
        choose_hf_slot([HFSlot("HF1"), HFSlot("HF1")])
