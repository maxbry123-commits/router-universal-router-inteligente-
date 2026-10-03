"""How a Router process starts on a Hugging Face Job (main 16 GB Router, elastic workers, mini router copies).

The code comes from a bundle in the HF bucket (RIU_CODE_BUNDLE, default buckets/COMAND-CENTER-1/yaiwes-memoria-storage/code/router-bundle.tar.gz),
so a Job never needs GitHub or a GitHub token. The same command is used by the Space micro-kernel (door) to launch/renew the main Router.
"""
from __future__ import annotations

import os

DEFAULT_BUNDLE = "buckets/COMAND-CENTER-1/yaiwes-memoria-storage/code/router-bundle.tar.gz"
PORT = 8000


def bundle_path() -> str:
    return os.getenv("RIU_CODE_BUNDLE") or DEFAULT_BUNDLE


def bootstrap_command(port: int = PORT, bundle: str | None = None) -> list[str]:
    """bash -lc command: fetch the bundle with HF_TOKEN, install deps, run the Router on `port`."""
    bundle = bundle or bundle_path()
    script = (
        "set -e; export HF_HUB_DISABLE_PROGRESS_BARS=1; pip install -q huggingface_hub >/dev/null; "
        "python - <<'PY'\n"
        "import io, os, tarfile\n"
        "from huggingface_hub import HfFileSystem\n"
        f"raw = HfFileSystem(token=os.environ['HF_TOKEN']).cat_file({bundle!r})\n"
        "tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz').extractall('/app')\n"
        "PY\n"
        "cd '/app/router inteligente universal' && "
        "pip install -q -r requirements.txt 'uvicorn[standard]' >/dev/null && "
        f"exec uvicorn integration.chat_mvp.app:app --host 0.0.0.0 --port {port} --timeout-keep-alive 120"
    )
    return ["bash", "-lc", script]


FORWARDED_SECRETS = (
    "HF_TOKEN", "HF_CONTROL_JOBS_TOKEN", "RIU_VAULT_PASSPHRASE", "RIU_AGENT_API_KEYS", "RIU_AGENT_API_KEYS_2", "RIU_ROUTER_API_KEY",
    "GITHUB_TOKEN", "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4",
    "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4", "GROQ_API_KEY_5", "GROQ_API_KEY_6", "GROQ_API_KEY_7",
    *[f"OPENAI_API_KEY_{i}" for i in range(1, 15)], "ANTHROPIC_API_KEY",
)


def forwarded_secrets() -> dict[str, str]:
    return {name: os.environ[name] for name in FORWARDED_SECRETS if os.getenv(name)}
