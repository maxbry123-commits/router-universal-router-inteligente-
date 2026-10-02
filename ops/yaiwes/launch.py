"""Launch one cpu-basic Job after verifying a real task and no active duplicate."""

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from github_store import GitHubStore

BOOT = r'''
set -eu
if ! command -v git >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y -qq git ca-certificates
fi
python -m pip install --no-cache-dir 'openai-agents==0.18.3' 'PyYAML==6.0.2'
git clone --filter=blob:none --sparse --depth=1 --single-branch --branch "$CODE_REF" "https://github.com/$REPO.git" /runner
git -C /runner sparse-checkout set ops/yaiwes
test "$(git -C /runner rev-parse HEAD)" = "$CODE_SHA"
exec python -u /runner/ops/yaiwes/supervisor.py
'''


def hf(method, route, token, data=None):
    payload = json.dumps(data).encode() if data is not None else None
    req = Request("https://huggingface.co/api/jobs/" + route, data=payload,
                  method=method, headers={"Authorization": "Bearer " + token,
                                          "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=45) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise RuntimeError("HF_JOBS_HTTP_" + str(exc.code)) from None


def launch(repo, queue_ref, model, github_token, openai_key, hf_token, namespace):
    if not model.startswith(("gpt-", "o1", "o3", "o4")):
        raise ValueError("ONLY_OPENAI_MODELS_ALLOWED")
    store = GitHubStore(repo, github_token)
    control = store.read("ops/yaiwes/control.json", queue_ref, missing=True)
    if control and json.loads(control).get("state") == "STOPPED_BY_DIRECTOR":
        raise RuntimeError("STOPPED_BY_DIRECTOR")
    agents = json.loads((Path(__file__).resolve().parent / "agents.json").read_text())
    if not any(store.requests(agent, queue_ref) for agent in agents):
        raise RuntimeError("NO_TASKS_NO_PAID_JOB")
    source_sha = store.ref(queue_ref)["object"]["sha"]
    current = hf("GET", namespace + "?" + urlencode({"label": "yaiwes=supervisor"}), hf_token)
    if any(item.get("status", {}).get("stage") in ("RUNNING", "SCHEDULING", "STARTING")
           for item in current):
        raise RuntimeError("SUPERVISOR_ALREADY_RUNNING")
    job = hf("POST", namespace, hf_token, {
        "dockerImage": "python:3.12", "command": ["bash", "-lc", BOOT],
        "arguments": [],
        "environment": {"REPO": repo, "QUEUE_REF": queue_ref, "CODE_REF": queue_ref,
                        "CODE_SHA": source_sha, "OPENAI_MODEL": model, "ADMIT_SECONDS": "21600"},
        "secrets": {"AGENT_GITHUB_TOKEN": github_token, "OPENAI_API_KEY": openai_key},
        "flavor": "cpu-basic", "timeoutSeconds": 25200,
        "labels": {"name": "yaiwes-nine-mvp", "yaiwes": "supervisor"},
    })
    return {"id": job["id"], "stage": job["status"]["stage"], "flavor": job.get("flavor")}


if __name__ == "__main__":
    print(json.dumps(launch(os.environ["REPO"], os.environ["QUEUE_REF"],
                            os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
                            os.environ["AGENT_GITHUB_TOKEN"], os.environ["OPENAI_API_KEY"],
                            os.environ["HF_TOKEN"], os.environ["HF_NAMESPACE"])))
