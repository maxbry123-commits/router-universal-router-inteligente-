"""hf_bootstrap.py — Descarga modelos, calcula sha256, actualiza registry.json."""
from __future__ import annotations
import hashlib, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE.parent / "llm system HF" / "registry.json"
MODELS_DIR = Path(os.getenv("HF_MODELS_DIR","./hf_models_cache"))

MODELS = {
    "s1": {"repo_id":"Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF",
            "file":"qwen2.5-coder-0.5b-instruct-q5_k_m.gguf"},
    "s2": {"repo_id":"LiquidAI/LFM2.5-350M-GGUF",
            "file":"LFM2.5-350M-Q4_K_M.gguf"},
    "s3": {"repo_id":"Qwen/Qwen3-0.6B-GGUF",
            "file":"Qwen3-0.6B-Q8_0.gguf"},
}

def _sha256_file(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    return h.hexdigest()

def download_one(space_id, repo_id, filename):
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        return {"space":space_id,"status":"degraded","reason":"huggingface_hub no instalado"}
    MODELS_DIR.mkdir(parents=True,exist_ok=True)
    try:
        local_dir = snapshot_download(repo_id=repo_id, allow_patterns=[filename],
                                      local_dir=str(MODELS_DIR/space_id), resume_download=True)
        local_path = Path(local_dir)/filename
        if not local_path.exists():
            return {"space":space_id,"status":"degraded","reason":f"archivo no encontrado: {filename}"}
        sha = _sha256_file(local_path)
        return {"space":space_id,"status":"ok","sha256":sha,
                "path":str(local_path),"bytes":local_path.stat().st_size}
    except Exception as exc:
        return {"space":space_id,"status":"degraded",
                "reason":type(exc).__name__+": "+str(exc)[:200]}

def update_registry(results):
    if not REGISTRY_PATH.exists():
        return {"status":"degraded","reason":f"registry.json no existe"}
    with open(REGISTRY_PATH,"r",encoding="utf-8") as f: reg = json.load(f)
    models = reg.setdefault("models",{})
    updated = []
    for sid,r in results.items():
        if r.get("status")=="ok" and sid in models:
            models[sid]["sha256"]=r["sha256"]; models[sid]["model_path"]=r["path"]
            updated.append(sid)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    with open(tmp,"w",encoding="utf-8") as f: json.dump(reg,f,indent=2,ensure_ascii=False)
    os.replace(tmp, REGISTRY_PATH)
    return {"status":"ok","updated":updated}

def run_bootstrap(dry_run=False):
    results = {}
    for sid,meta in MODELS.items():
        if dry_run:
            results[sid]={"space":sid,"status":"dry_run",
                          "repo_id":meta["repo_id"],"file":meta["file"]}
            continue
        results[sid]=download_one(sid, meta["repo_id"], meta["file"])
    ok = sum(1 for r in results.values() if r.get("status")=="ok")
    reg_result = update_registry(results) if (not dry_run and ok>0) else {"status":"skipped"}
    return {"descargados":ok,"total":len(MODELS),
            "registry":reg_result,"results":results}

if __name__=="__main__":
    dry = "--dry-run" in sys.argv
    r = run_bootstrap(dry_run=dry)
    print(json.dumps(r,indent=2,ensure_ascii=False))
    sys.exit(0 if r["descargados"]==r["total"] else 1)
