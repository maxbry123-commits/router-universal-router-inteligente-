"""
artifact_registry.py — Registro de artefactos en Bucket Hugging Face
Ubicacion: external/tools/artifact_registry.py
Regla: Spaces stateless; artefactos (MD, ZIP, JSON) persisten en bucket.
Uso de huggingface_hub: upload_file / hf_hub_download con repo_type="dataset".
"""
from __future__ import annotations
import logging
import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

HF_REPO = os.getenv("HF_ARTIFACTS_REPO", "COMAND-CENTER-1/artifacts")
HF_TYPE = os.getenv("HF_ARTIFACTS_TYPE", "dataset")
LOCAL_CACHE = Path(os.getenv("ARTIFACT_CACHE", "./artifact_cache"))


class ArtifactRegistry:
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("HF_TOKEN")
        LOCAL_CACHE.mkdir(parents=True, exist_ok=True)

    def _api(self):
        from huggingface_hub import HfApi
        return HfApi(token=self.token)

    def publish(self, local_path: str, remote_path: str,
                commit_message: str = "artifact") -> Dict[str, Any]:
        lp = Path(local_path)
        if not lp.exists():
            raise FileNotFoundError(local_path)
        api = self._api()
        api.upload_file(
            path_or_fileobj=str(lp),
            path_in_repo=remote_path,
            repo_id=HF_REPO,
            repo_type=HF_TYPE,
            commit_message=commit_message,
        )
        logger.info("Artifact publicado %s -> hf://%s/%s", local_path, HF_REPO, remote_path)
        return {"status": "published", "remote": f"hf://{HF_REPO}/{remote_path}",
                "sha256": self._sha256(str(lp))}

    def fetch(self, remote_path: str, local_path: Optional[str] = None) -> str:
        from huggingface_hub import hf_hub_download
        dest = local_path or str(LOCAL_CACHE / Path(remote_path).name)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        out = hf_hub_download(
            repo_id=HF_REPO, repo_type=HF_TYPE,
            filename=remote_path, local_dir=str(LOCAL_CACHE),
            token=self.token,
        )
        logger.info("Artifact recuperado %s -> %s", remote_path, out)
        return out

    def list_artifacts(self) -> List[str]:
        api = self._api()
        files = api.list_repo_files(repo_id=HF_REPO, repo_type=HF_TYPE)
        return [f for f in files if not f.startswith(".")]

    def index(self) -> Dict[str, Any]:
        items = self.list_artifacts()
        return {
            "repo": HF_REPO, "type": HF_TYPE,
            "count": len(items), "files": items,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    @staticmethod
    def _sha256(path: str) -> str:
        import hashlib
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
