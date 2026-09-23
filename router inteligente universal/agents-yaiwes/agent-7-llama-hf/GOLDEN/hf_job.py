def build_hf_job(repo, gguf_file, slots=4, ctx_per_slot=4096, flavor="cpu-upgrade", port=8080, kv="q8_0", cache_ram_mb=512):
    # Validar formato del repo: "organizacion/nombre"
    if '/' not in repo:
        raise ValueError(f"repo must be in format 'organizacion/nombre', got '{repo}'")
    parts = repo.split('/', 1)
    if not parts[0] or not parts[1]:
        raise ValueError(f"repo must be in format 'organizacion/nombre', got '{repo}'")
    if '/' in parts[1]:
        raise ValueError(f"repo must be in format 'organizacion/nombre' (exactly one slash), got '{repo}'")

    # Validar otros parametros
    if kv not in ("f16", "q8_0", "q4_0"):
        raise ValueError(f"kv must be one of 'f16', 'q8_0', 'q4_0', got '{kv}'")
    if slots < 1:
        raise ValueError(f"slots must be >= 1, got {slots}")
    if ctx_per_slot < 512:
        raise ValueError(f"ctx_per_slot must be >= 512, got {ctx_per_slot}")

    total_ctx = slots * ctx_per_slot

    command = [
        "llama-server",
        "-m", f"/model/{gguf_file}",
        "--host", "0.0.0.0",
        "--port", str(port),
        "-c", str(total_ctx),
        "-np", str(slots),
        "-cb",
        "--cache-prompt",
        "--cache-reuse", "256",
        "--cache-ram", str(cache_ram_mb),
        "-fa", "on",
        "-ctk", kv,
        "-ctv", kv,
    ]

    return {
        "image": "ghcr.io/ggml-org/llama.cpp:server",
        "flavor": flavor,
        "expose": [port],
        "volumes": [f"hf://models/{repo}:/model:ro"],
        "command": command,
    }
