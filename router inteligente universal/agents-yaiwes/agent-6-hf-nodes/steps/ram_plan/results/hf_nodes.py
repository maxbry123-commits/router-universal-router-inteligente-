# hf_nodes.py

from typing import Optional

NODES = [{"id": f"HF-{i:02d}", "ram_gb": 32, "vcpu": 8} for i in range(1, 11)]

def kv_cache_mb(n_layers: int, n_kv_heads: int, head_dim: int, ctx_tokens: int, bytes_per_elem: float) -> float:
    return 2 * n_layers * n_kv_heads * head_dim * ctx_tokens * bytes_per_elem / 1e6

def plan_slots(weights_mb: float, kv_mb_per_slot: float, slots: int, ram_cap_mb: float, overhead_mb: float = 1500) -> dict:
    total_mb = weights_mb + slots * kv_mb_per_slot + overhead_mb
    fits = total_mb <= ram_cap_mb
    max_slots = 0
    if kv_mb_per_slot > 0:
        max_slots = max(0, int((ram_cap_mb - weights_mb - overhead_mb) // kv_mb_per_slot))
    elif ram_cap_mb >= weights_mb + overhead_mb:
        max_slots = slots  # any number fits if kv is zero
    return {
        "total_mb": total_mb,
        "fits": fits,
        "max_slots": max_slots
    }

def reduce_ctx_to_fit(weights_mb: float, kv_mb_per_1k_tokens: float, slots: int, ram_cap_mb: float,
                      ctx_start: int = 8192, ctx_min: int = 2048, overhead_mb: float = 1500) -> Optional[int]:
    ctx = ctx_start
    while ctx >= ctx_min:
        kv_slot = kv_mb_per_1k_tokens * ctx / 1000
        total = weights_mb + slots * kv_slot + overhead_mb
        if total <= ram_cap_mb:
            return ctx
        ctx //= 2
    return None
