#!/usr/bin/env python3
"""Dedicated canonical downloader for OpenClaw + Rowboat.
Hard constraints: NO Git LFS, NO GitHub Actions, NO Hugging Face.
Uses the repository's canonical download/extract engine directly.
"""
from __future__ import annotations
import json, os, pathlib, subprocess, sys

HERE=pathlib.Path(__file__).resolve().parent
ENGINE=HERE/"hf_download_extract_engine.py"
DEST_REPO="maxbry123-commits/router-universal-router-inteligente-"
DEST_BRANCH="main"

COMPONENTS=[
  {"slug":"openclaw","source_repo":"openclaw/openclaw","source_ref":"v2026.9.5"},
  {"slug":"rowboat","source_repo":"rowboatlabs/rowboat","source_ref":"main"},
]

FORBIDDEN=("git-lfs","git lfs","huggingface","hugging face","hf job","github actions","workflow_dispatch")

def run_one(c):
    env=dict(os.environ)
    env.update({
      "SOURCE_REPO":c["source_repo"],"SOURCE_REF":c["source_ref"],"SLUG":c["slug"],
      "DEST_REPO":DEST_REPO,"DEST_BRANCH":DEST_BRANCH,"DEST_ROOT":".",
      "PUBLISH":"1","PART_SIZE_MIB":"12","MAX_GITHUB_BLOB_MIB":"95",
      "GIT_LFS_SKIP_SMUDGE":"1",
    })
    p=subprocess.run([sys.executable,str(ENGINE)],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    out=p.stdout.strip()
    if any(x in out.lower() for x in FORBIDDEN):
        raise RuntimeError(f"FORBIDDEN_BACKEND_REFERENCE:{c['slug']}")
    if p.returncode:
        raise RuntimeError(f"{c['slug']}:ENGINE_FAILED:{out[-5000:]}")
    result=json.loads(out.splitlines()[-1])
    if result.get("no_lfs") is not True:
        raise RuntimeError(f"{c['slug']}:NO_LFS_ASSERTION_FAILED")
    if result.get("reconstruction_verified") is not True or result.get("extraction_verified") is not True:
        raise RuntimeError(f"{c['slug']}:VERIFICATION_FAILED")
    if result.get("publish",{}).get("verdict")!="PUBLISHED_AND_EXTRACTED_READBACK_VERIFIED":
        raise RuntimeError(f"{c['slug']}:READBACK_FAILED")
    if result.get("verdict")!="VERIFIED_CLOSED":
        raise RuntimeError(f"{c['slug']}:NOT_VERIFIED_CLOSED")
    return result

def main():
    if not ENGINE.is_file(): raise SystemExit("CANONICAL_ENGINE_MISSING")
    results=[]
    for c in COMPONENTS:
        try: results.append({"slug":c["slug"],"status":"VERIFIED_CLOSED","result":run_one(c)})
        except Exception as e:
            results.append({"slug":c["slug"],"status":"FAILED","error":str(e)})
    print(json.dumps({"schema":"yaiwes.direct-motor.no-lfs.v1","constraints":{"lfs":False,"github_actions":False,"huggingface":False},"results":results},ensure_ascii=False))
    if any(x["status"]!="VERIFIED_CLOSED" for x in results): raise SystemExit(1)
if __name__=="__main__": main()
