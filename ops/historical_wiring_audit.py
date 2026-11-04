import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from huggingface_hub import HfApi, upload_folder

REPO = os.environ["GH_REPO"]
BRANCH = os.getenv("GH_BRANCH", "main")
REPORT_REPO = os.environ["HF_REPORT_REPO"]

GH_TOKEN = os.environ["GH_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

MAX_COMMITS = int(os.getenv("MAX_COMMITS", "500"))

WORK = Path("/tmp/wiring-audit")
SRC = WORK / "source"
OUT = WORK / "output"

OUT.mkdir(parents=True, exist_ok=True)


def git(args, check=True):
    return subprocess.run(
        ["git"] + args,
        cwd=SRC,
        text=True,
        capture_output=True,
        check=check
    ).stdout


def redact(text):
    text = re.sub(
        r"(?i)(token|password|secret|api_key)"
        r"(\s*[:=]\s*)['\"]?[^'\"\s,]+",
        r"\1\2[REDACTED]",
        text
    )
    text = re.sub(
        r"(https?://)[^/@\s]+@",
        r"\1[REDACTED]@",
        text
    )
    return text[:400]


def save(name, data):
    (OUT / name).write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )


# 1. Clonar historial completo disponible
url = (
    f"https://x-access-token:{GH_TOKEN}"
    f"@github.com/{REPO}.git"
)

subprocess.run(
    ["git", "clone", "--no-single-branch", url, str(SRC)],
    check=True
)

git(["remote", "set-url", "origin",
     f"https://github.com/{REPO}.git"])

git(["fetch", "--all", "--tags", "--prune"])

head = git(["rev-parse", f"origin/{BRANCH}"]).strip()

# 2. Obtener commits de todas las referencias
commits = git([
    "rev-list", "--all", f"--max-count={MAX_COMMITS}"
]).splitlines()

historical = []
current = []

patterns = {
    "http": r"https?://|fetch\(|axios|requests\.|httpx|aiohttp",
    "mcp": r"\bMCP\b|tools/list|tools/call|streamable|stdio",
    "endpoints": r"BASE_URL|API_URL|ENDPOINT|SERVICE_URL|/api/",
    "agents": r"agent|orchestrator|specialist|handoff",
    "engines": r"hermes|deepseek|engine|provider",
    "imports": r"^\s*(import |from |require\()"
}

# 3. Examinar referencias en cada versión
for index, commit in enumerate(commits):

    metadata = git([
        "show", "-s",
        "--format=%H%x1f%ad%x1f%s",
        "--date=iso-strict", commit
    ]).strip().split("\x1f")

    record = {
        "commit": commit,
        "date": metadata[1] if len(metadata) > 1 else "",
        "message": metadata[2] if len(metadata) > 2 else "",
        "references": []
    }

    for category, pattern in patterns.items():

        result = subprocess.run(
            ["git", "grep", "-n", "-I", "-E",
             pattern, commit, "--",
             ".", ":!*.lock", ":!*.map"],
            cwd=SRC,
            text=True,
            capture_output=True
        )

        for line in result.stdout.splitlines():
            record["references"].append({
                "category": category,
                "reference": redact(line)
            })

    historical.append(record)

    if commit == head:
        current = record["references"]

# 4. Comparar referencias históricas y actuales
current_set = {
    x["category"] + "|" + x["reference"].split(":", 1)[-1]
    for x in current
}

historical_set = {}

for record in historical:
    for ref in record["references"]:
        key = (
            ref["category"] + "|" +
            ref["reference"].split(":", 1)[-1]
        )
        historical_set.setdefault(key, []).append(
            record["commit"]
        )

removed = [
    {
        "reference": key,
        "commits": commits
    }
    for key, commits in historical_set.items()
    if key not in current_set
]

# 5. Historial de archivos eliminados y renombrados
changes = git([
    "log", "--all", "--name-status",
    "--format=%H|%ad|%s", "--date=iso"
])

(OUT / "file_history.txt").write_text(changes)

# 6. Generar informes
save("historical_connections.json", historical)
save("current_connections.json", current)
save("removed_candidates.json", removed)

save("summary.json", {
    "repository": REPO,
    "branch": BRANCH,
    "head": head,
    "commits_examined": len(commits),
    "historical_references": len(historical_set),
    "current_references": len(current),
    "removed_candidates": len(removed),
    "generated_at": datetime.now(timezone.utc).isoformat()
})

# 7. Persistir en Hugging Face
api = HfApi(token=HF_TOKEN)

upload_folder(
    folder_path=str(OUT),
    repo_id=REPORT_REPO,
    repo_type="dataset",
    path_in_repo=f"wiring/{head}"
)

print("HISTORICAL WIRING AUDIT COMPLETED")
print("Commits:", len(commits))
print("Candidates:", len(removed))
print("HEAD:", head)
