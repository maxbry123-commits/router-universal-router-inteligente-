import os
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime, timezone
from huggingface_hub import HfApi, upload_folder

GH_REPO = os.environ["GH_REPO"]
GH_BRANCH = os.getenv("GH_BRANCH", "main")
HF_REPO = os.environ["HF_REPO"]

GH_TOKEN = os.environ["GH_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

WORK = Path(os.environ.get("WORK_DIR","/workspace/work"))/"router-audit"
SOURCE = WORK / "source"
REPORT = WORK / "report"

WORK.mkdir(parents=True, exist_ok=True)
REPORT.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True
    ).stdout


# 1. Clonar GitHub conservando historial
url = f"https://x-access-token:{GH_TOKEN}@github.com/{GH_REPO}.git"

run([
    "git", "clone", "--no-single-branch",
    url, str(SOURCE)
])

run(["git", "fetch", "--all", "--tags"], cwd=SOURCE)

# 2. Estado actual
commit = run(
    ["git", "rev-parse", "HEAD"], cwd=SOURCE
).strip()

tree = run(
    ["git", "ls-files"], cwd=SOURCE
).splitlines()

# 3. Historial
history = run(
    ["git", "log", "--all", "--date=iso",
     "--name-status", "--format=%H|%ad|%s"],
    cwd=SOURCE
)

(REPORT / "git_history.txt").write_text(history)

# 4. Detectar referencias de conectividad
patterns = {
    "http": r"https?://[^\s\"'<>]+",
    "environment": r"\b[A-Z][A-Z0-9_]*(?:URL|URI|HOST|ENDPOINT|TOKEN)\b",
    "mcp": r"\bMCP\b|tools/list|tools/call|stdio|streamable",
    "imports": r"^\s*(?:import |from |require\()",
    "network": r"fetch\(|axios\.|requests\.|httpx\.|aiohttp"
}

findings = []

for path in SOURCE.rglob("*"):
    if not path.is_file():
        continue

    if any(x in path.parts for x in [
        ".git", "node_modules", ".venv", "__pycache__"
    ]):
        continue

    try:
        content = path.read_text(errors="ignore")
    except Exception:
        continue

    for category, pattern in patterns.items():
        for number, line in enumerate(content.splitlines(), 1):
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    "file": str(path.relative_to(SOURCE)),
                    "line": number,
                    "category": category,
                    "reference": line.strip()[:500]
                })

# 5. Generar registro
registry = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "repository": GH_REPO,
    "branch": GH_BRANCH,
    "commit": commit,
    "files": tree,
    "findings": findings,
    "status": "discovered_not_runtime_verified"
}

(REPORT / "registry.json").write_text(
    json.dumps(registry, indent=2, ensure_ascii=False)
)

# 6. Inventario de ramas y commits
branches = run(
    ["git", "branch", "-a"], cwd=SOURCE
)

(REPORT / "branches.txt").write_text(branches)

# 7. Subir auditoría a Hugging Face
api = HfApi(token=HF_TOKEN)

upload_folder(
    folder_path=str(REPORT),
    repo_id=HF_REPO,
    repo_type="dataset",
    path_in_repo=f"audits/{commit}"
)

print("AUDITORÍA COMPLETADA")
print("Commit:", commit)
print("Archivos:", len(tree))
print("Referencias:", len(findings))
print("Informe:", f"audits/{commit}")
