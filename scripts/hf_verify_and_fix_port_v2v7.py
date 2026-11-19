"""hf_verify_and_fix_port_v2v7.py — Inserta app_port:7860 en v2 y v7.
Idempotente. --verify-only no escribe, solo comprueba.

ADAPTACION 1 (nombrado): los Spaces se renombraron el 2026-11-18 ->
space-grupo-1-router-mvp-1-v2 / -v7 (los nombres local-llm-router-v2/-v7 ya no existen).
ADAPTACION 2 (token): acepta HF_TOKEN o HF_TOKEN_1_NEW.
"""
import os, re, sys, tempfile
from huggingface_hub import HfApi, hf_hub_download

SPACES = ["COMAND-CENTER-1/space-grupo-1-router-mvp-1-v2", "COMAND-CENTER-1/space-grupo-1-router-mvp-1-v7"]
TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_TOKEN_1_NEW")
api = HfApi(token=TOKEN)
VERIFY_ONLY = "--verify-only" in sys.argv
FAILED = []

def has_port(txt: str) -> bool:
    return bool(re.search(r"^\s*app_port:\s*7860\s*$", txt, re.M))

def inject(txt: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
    if m:
        return f"---\n{m.group(1)}\napp_port: 7860\n---\n" + txt[m.end():]
    return f"---\napp_port: 7860\n---\n" + txt

for space in SPACES:
    tag = space.rsplit("-", 1)[-1].upper()
    try:
        p = hf_hub_download(repo_id=space, filename="README.md",
                            repo_type="space", token=TOKEN)
        txt = open(p, encoding="utf-8").read()
        if has_port(txt):
            print(f"PORT_OK_{tag}"); continue
        if VERIFY_ONLY:
            print(f"PORT_MISSING_{tag}"); FAILED.append(tag); continue
        new = inject(txt)
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(new); tmp = f.name
        api.upload_file(path_or_fileobj=tmp, path_in_repo="README.md",
                        repo_id=space, repo_type="space", token=TOKEN)
        print(f"PORT_FIXED_{tag}")
    except Exception as e:
        print(f"ERROR_{tag}: {e}"); FAILED.append(tag)

sys.exit(1 if FAILED else 0)
