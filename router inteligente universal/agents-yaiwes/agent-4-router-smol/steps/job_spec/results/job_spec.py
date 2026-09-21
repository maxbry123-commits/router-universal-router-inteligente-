def build_job_spec(repo: str, gguf_file: str, port: int = 8080, flavor: str = "cpu-upgrade", parallel: int = 4, ctx: int = 8192) -> dict:
    if "/" not in repo or repo.count("/") != 1 or not repo.split("/")[0] or not repo.split("/")[1]:
        raise ValueError(f"repo must have the form 'organizacion/nombre', got {repo!r}")
    return {
        "image": "ghcr.io/ggml-org/llama.cpp:server",
        "flavor": flavor,
        "expose": port,
        "volumes": [f"hf://models/{repo}:/model:ro"],
        "command": [
            "llama-server",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--model", f"/model/{gguf_file}",
            "--parallel", str(parallel),
            "--ctx-size", str(ctx),
            "--cont-batching",
            "--cache-prompt"
        ]
    }
