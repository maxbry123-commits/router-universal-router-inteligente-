"""hf_setup_spaces.py — Crea o verifica los Spaces s1/s2/s3 en Hugging Face."""
from __future__ import annotations
import argparse, json, os, sys
from typing import Any

SPACES = {
    "s1": {"model_id":"Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
            "model_file":"qwen2.5-coder-0.5b-instruct-q5_k_m.gguf"},
    "s2": {"model_id":"LiquidAI/LFM2.5-350M-GGUF",
            "model_file":"LFM2.5-350M-Q4_K_M.gguf"},
    "s3": {"model_id":"Qwen/Qwen3-0.6B-GGUF",
            "model_file":"Qwen3-0.6B-Q8_0.gguf"},
}
GITHUB_BRANCH = "ccr-f01c3de9-bmry0s"

def _api():
    token = os.getenv("HF_TOKEN")
    if not token: raise RuntimeError("HF_TOKEN no configurada")
    from huggingface_hub import HfApi
    return HfApi(token=token)

def setup_one_space(api, namespace, space_id, meta):
    full_id = f"{namespace}/{space_id}"
    result = {"space":full_id}
    try:
        api.get_space_info(full_id, repo_type="space")
        result["exists"] = True
    except Exception:
        result["exists"] = False
    if not result["exists"]:
        try:
            api.create_repo(repo_id=full_id, repo_type="space",
                            space_sdk="docker", private=True, exist_ok=True)
            result["created"] = True
        except Exception as exc:
            result["created"] = False
            result["error"] = f"create: {type(exc).__name__}"
            return result
    secrets = {
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN",""),
        "GITHUB_BRANCH": GITHUB_BRANCH,
        "ROUTER_API_KEY": os.getenv("ROUTER_API_KEY",""),
        "MODEL_ID": meta["model_id"],
        "MODEL_FILE": meta["model_file"],
        "MODEL_PATH": f"/data/models/{meta['model_file']}",
        "SPACE_ID": space_id,
    }
    try:
        for key,value in secrets.items():
            if value: api.add_space_secret(full_id, key, value)
        result["secrets_set"] = list(secrets.keys())
    except Exception as exc:
        result["secrets_error"] = type(exc).__name__
    return result

def run_setup(namespace):
    api = _api()
    results = {}
    for sid,meta in SPACES.items():
        results[sid] = setup_one_space(api, namespace, sid, meta)
    ok = sum(1 for r in results.values() if r.get("exists") or r.get("created"))
    return {"namespace":namespace,"spaces_ok":ok,
            "spaces_total":len(SPACES),"results":results}

if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", default=os.getenv("HF_NAMESPACE",""))
    a = ap.parse_args()
    if not a.namespace:
        print("ERROR: pasar --namespace o fijar HF_NAMESPACE"); sys.exit(2)
    r = run_setup(a.namespace)
    print(json.dumps(r,indent=2,ensure_ascii=False))
    sys.exit(0 if r["spaces_ok"]==r["spaces_total"] else 1)
