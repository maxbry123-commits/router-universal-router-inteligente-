import os
import json
import hashlib
from pathlib import Path
from huggingface_hub import snapshot_download

SPACE_ID = "COMAND-CENTER-1/local-llm-router-v7"
TARGET = Path("ROUTER MVP v1/hf_snapshot")

try:
    snapshot_download(
        repo_id=SPACE_ID,
        repo_type="space",
        local_dir=str(TARGET),
        local_dir_use_symlinks=False
    )
    manifest = {}
    for root, _, files in os.walk(TARGET):
        for f in files:
            p = Path(root) / f
            rel = str(p.relative_to(TARGET))
            if rel.startswith("audit/") or rel == "manifest.json":
                continue
            # [FIX-DAG-v2/1] snapshot_download() con local_dir= deja 23 ficheros de metadatos
            #   locales en .cache/huggingface/ (CACHEDIR.TAG, .gitignore, download/*.lock,
            #   download/*.metadata, trees/<sha>.json). NO son contenido del Space y no existen
            #   en el remoto: sin esta exclusion el manifiesto daba local=33 vs remoto=9 y el
            #   Sheriff hacia NO_GO con "no se pudo leer remoto .cache/huggingface/.gitignore: 404".
            # [FIX-DAG-v2/2] centinel_job.py y sheriff_job.py YA excluyen ".gitattributes" de la
            #   lista remota; aqui se excluye tambien del manifiesto local para que la
            #   comparacion sea simetrica (si no, extra_local = ['.gitattributes'] -> NO_GO).
            if rel.startswith(".cache/") or rel == ".gitattributes":
                continue
            manifest[rel] = {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size
            }
    (TARGET / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[DOWNLOAD] OK archivos={len(manifest)}")
except Exception as e:
    print(f"[DOWNLOAD] FAIL {e}")
    raise SystemExit(1)
