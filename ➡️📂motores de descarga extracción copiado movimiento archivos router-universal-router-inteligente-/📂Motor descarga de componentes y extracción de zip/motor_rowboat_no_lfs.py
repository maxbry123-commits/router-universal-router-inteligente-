#!/usr/bin/env python3
"""Rowboat-only canonical motor. NO LFS, NO GitHub Actions, NO Hugging Face."""
from __future__ import annotations
import json, os, pathlib, subprocess, sys
HERE=pathlib.Path(__file__).resolve().parent
ENGINE=HERE/'hf_download_extract_engine.py'
env=dict(os.environ)
env.update({'SOURCE_REPO':'rowboatlabs/rowboat','SOURCE_REF':'main','SLUG':'rowboat','DEST_REPO':'maxbry123-commits/router-universal-router-inteligente-','DEST_BRANCH':'main','DEST_ROOT':'.','PUBLISH':'1','PART_SIZE_MIB':'12','MAX_GITHUB_BLOB_MIB':'95','GIT_LFS_SKIP_SMUDGE':'1'})
p=subprocess.run([sys.executable,str(ENGINE)],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(p.stdout,end='')
if p.returncode: raise SystemExit(p.returncode)
r=json.loads(p.stdout.strip().splitlines()[-1])
assert r.get('no_lfs') is True
assert r.get('reconstruction_verified') is True
assert r.get('extraction_verified') is True
assert r.get('publish',{}).get('verdict')=='PUBLISHED_AND_EXTRACTED_READBACK_VERIFIED'
assert r.get('verdict')=='VERIFIED_CLOSED'
