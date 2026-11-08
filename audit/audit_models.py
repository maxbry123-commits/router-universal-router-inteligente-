import os, json
from huggingface_hub import HfApi

USER = "COMAND-CENTER-1"
api = HfApi(token=os.environ.get("HF_TOKEN"))
out = {"models": {}, "triggers": {}, "spaces_meta": {}}

# 1. Inspeccionar los 3 modelos locales
for sp_id in ["COMAND-CENTER-1/swe-code-s1",
              "COMAND-CENTER-1/swe-code-s2",
              "COMAND-CENTER-1/swe-code-s3"]:
    out["models"][sp_id] = {}
    try:
        files = api.list_repo_files(repo_id=sp_id, repo_type="space")
        for target in ["README.md", "Dockerfile", "manager.py", "scaler.py",
                       "fetch_models.py", "entrypoint.sh"]:
            matches = [p for p in files if p == target or p.endswith("/" + target)]
            for rel in matches:
                path = api.hf_hub_download(repo_id=sp_id, repo_type="space", filename=rel)
                content = open(path, "r", encoding="utf-8", errors="ignore").read()
                out["models"][sp_id][rel] = content[:1500]
    except Exception as e:
        out["models"][sp_id]["error"] = str(e)

# 2. Buscar quién dispara fleet.py / mini.py / manager / scaler
#    (buscar endpoints tipo /mini/, /fleet/, /v1/, /manager/, /scale)
SEARCH = ["fleet", "mini", "/mini/", "/fleet/", "manager", "scaler",
          "run_job", "run_jobs", "api/jobs", "/v1/chat", "/v1/models"]
for sp_id in ["COMAND-CENTER-1/riu-router",
              "COMAND-CENTER-1/claude-github-mcp-backup",
              "COMAND-CENTER-1/swe-code-web"]:
    out["triggers"][sp_id] = []
    try:
        files = api.list_repo_files(repo_id=sp_id, repo_type="space")
        for f in files:
            if not (f.endswith(".py") or f.endswith(".js") or f.endswith(".sh")):
                continue
            try:
                path = api.hf_hub_download(repo_id=sp_id, repo_type="space", filename=f)
                content = open(path, "r", encoding="utf-8", errors="ignore").read()
                for kw in SEARCH:
                    if kw in content:
                        out["triggers"][sp_id].append({"file": f, "found": kw})
                        break
            except Exception:
                pass
    except Exception as e:
        out["triggers"][sp_id].append({"error": str(e)})

# 3. Metadata de los Spaces (hardware, sdk, stage)
for sp_id in ["COMAND-CENTER-1/swe-code-s1",
              "COMAND-CENTER-1/swe-code-s2",
              "COMAND-CENTER-1/swe-code-s3",
              "COMAND-CENTER-1/riu-router",
              "COMAND-CENTER-1/claude-github-mcp-backup",
              "COMAND-CENTER-1/swe-code-web"]:
    try:
        info = api.space_info(repo_id=sp_id)
        hw = info.runtime.hardware if info.runtime else None
        hw = hw.get("current") if isinstance(hw, dict) else hw
        out["spaces_meta"][sp_id] = {
            "sdk": info.sdk,
            "hardware": hw,
            "stage": info.runtime.stage if info.runtime else None
        }
    except Exception as e:
        out["spaces_meta"][sp_id] = {"error": str(e)}

with open("audit/audit_models.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

print("===AUDIT_COMPLETADA===")
print(json.dumps(out, indent=2))
