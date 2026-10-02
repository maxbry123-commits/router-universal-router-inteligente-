"""GitHub task queue and atomic, read-back-checked task checkpoints."""

import base64
import json
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from contracts import IDENTIFIER, ROOT


class GitHubStore:
    def __init__(self, repo, token):
        if not repo or len(repo.split("/")) != 2 or not token:
            raise ValueError("INVALID_GITHUB_CONFIG")
        self.repo = repo
        self.token = token
        self.api = "https://api.github.com/repos/" + repo

    def request(self, method, route, data=None, missing=False):
        payload = json.dumps(data).encode() if data is not None else None
        req = Request(self.api + route, data=payload, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        })
        try:
            with urlopen(req, timeout=45) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as exc:
            if missing and exc.code == 404:
                return None
            raise RuntimeError("GitHub HTTP " + str(exc.code)) from None

    def read(self, name, ref, missing=False):
        route = "/contents/" + quote(name, safe="/") + "?" + urlencode({"ref": ref})
        item = self.request("GET", route, missing=missing)
        if item is None:
            return None
        if not isinstance(item, dict) or item.get("encoding") != "base64" or item.get("type") != "file":
            raise RuntimeError("INVALID_GITHUB_FILE")
        return base64.b64decode(item["content"]).decode("utf-8")

    def requests(self, agent_id, ref):
        if not IDENTIFIER.fullmatch(agent_id):
            raise ValueError("INVALID_AGENT_ID")
        route = "/contents/" + quote(f"{ROOT}/{agent_id}/requests", safe="/") + "?" + urlencode({"ref": ref})
        listing = self.request("GET", route, missing=True) or []
        if not isinstance(listing, list):
            raise RuntimeError("INVALID_GITHUB_DIRECTORY")
        return sorted(item["name"] for item in listing if item.get("type") == "dir" and
                      IDENTIFIER.fullmatch(item.get("name", "")))

    def ref(self, branch, missing=False):
        return self.request("GET", "/git/ref/heads/" + quote(branch, safe="/"), missing=missing)

    def claim(self, branch, source_sha):
        existing = self.ref(branch, missing=True)
        if existing:
            return existing["object"]["sha"], False
        self.request("POST", "/git/refs", {"ref": "refs/heads/" + branch, "sha": source_sha})
        claimed = self.ref(branch)
        if claimed["object"]["sha"] != source_sha:
            raise RuntimeError("CLAIM_READBACK_MISMATCH")
        return source_sha, True

    def checkpoint(self, branch, parent, files, message):
        current = self.ref(branch)
        if current["object"]["sha"] != parent:
            raise RuntimeError("CHECKPOINT_CONCURRENT_UPDATE")
        commit = self.request("GET", "/git/commits/" + parent)
        tree = []
        for name, content in sorted(files.items()):
            if not isinstance(content, str):
                raise ValueError("INVALID_CHECKPOINT_CONTENT")
            blob = self.request("POST", "/git/blobs", {"content": content, "encoding": "utf-8"})
            tree.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        new_tree = self.request("POST", "/git/trees", {"base_tree": commit["tree"]["sha"], "tree": tree})
        new_commit = self.request("POST", "/git/commits", {
            "message": message, "tree": new_tree["sha"], "parents": [parent],
        })
        sha = new_commit["sha"]
        self.request("PATCH", "/git/refs/heads/" + quote(branch, safe="/"), {"sha": sha, "force": False})
        if self.ref(branch)["object"]["sha"] != sha:
            raise RuntimeError("CHECKPOINT_REF_READBACK_MISMATCH")
        for name, content in files.items():
            if self.read(name, sha) != content:
                raise RuntimeError("CHECKPOINT_FILE_READBACK_MISMATCH")
        return sha

    def pull_request(self, branch, request_id):
        owner = self.repo.split("/")[0]
        route = "/pulls?" + urlencode({"state": "open", "head": owner + ":" + branch, "base": "main"})
        existing = self.request("GET", route)
        if existing:
            return existing[0]["html_url"]
        pr = self.request("POST", "/pulls", {
            "title": "YAIWES " + request_id,
            "head": branch,
            "base": "main",
            "body": "Job HF cpu-basic: código y comprobantes en la rama. Pendiente de revisión; no se ha hecho merge.",
        })
        return pr["html_url"]
