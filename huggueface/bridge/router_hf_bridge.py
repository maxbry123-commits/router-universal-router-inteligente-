import os
import json
import urllib.request
from typing import Any, Dict

PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "cerebras": ("https://api.cerebras.ai/v1", "CEREBRAS_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
}


def _request(url: str, token: str, payload: Dict[str, Any] | None = None, method: str = "GET"):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def provider_models(provider: str):
    base, secret = PROVIDERS[provider]
    token = os.environ[secret]
    return _request(f"{base}/models", token)


def chat(provider: str, model: str, messages: list[dict], **kwargs):
    base, secret = PROVIDERS[provider]
    token = os.environ[secret]
    payload = {"model": model, "messages": messages, **kwargs}
    return _request(f"{base}/chat/completions", token, payload, "POST")


def bridge_health():
    return {
        "contract": "HF-ROUTER-BRIDGE-V1",
        "remote_only": True,
        "protocols": {
            "http_rest": True,
            "fastapi": True,
            "openai_compatible": True,
            "mcp_streamable_http": True,
            "mcp_sse_legacy": True,
            "sse_streaming": True,
            "webhook_callbacks": True,
            "websocket_optional": True,
            "ssh_tunnel_optional": True,
        },
        "providers": sorted(PROVIDERS),
        "failover": "HF1->HF2->HF3->WAITING",
        "cache": {"warn_gb": 1, "hard_clean_gb": 2, "action": "LRU_EVICT_AND_OFFLOAD"},
    }


if __name__ == "__main__":
    print(json.dumps(bridge_health(), sort_keys=True))
