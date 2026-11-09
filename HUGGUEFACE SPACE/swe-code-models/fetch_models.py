#!/usr/bin/env python3
import os, sys
from pathlib import Path
from huggingface_hub import hf_hub_download

dataset = os.environ.get("GGUF_DATASET", "COMAND-CENTER-1/swe-code-hf-gguf")
token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
out = Path(os.environ.get("MODEL_DIR", "/data/models"))
out.mkdir(parents=True, exist_ok=True)
files = [f for f in os.environ.get("GGUF_FILES", "").split(",") if f.strip()]
if not files:
    print("GGUF_FILES empty", file=sys.stderr); sys.exit(1)
if not token:
    print("HF_TOKEN missing", file=sys.stderr); sys.exit(1)
paths = []
for f in files:
    f = f.strip()
    p = hf_hub_download(repo_id=dataset, repo_type="dataset", filename=f, local_dir=str(out), token=token)
    print("DOWNLOADED", f, "->", p, flush=True)
    paths.append(p)
Path("/tmp/model_paths.txt").write_text("\n".join(paths) + "\n")
