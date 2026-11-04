import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from huggingface_hub import upload_folder

REPO = os.environ["GH_REPO"]
BRANCH = os.getenv("GH_BRANCH", "main")
REPORT_REPO = os.environ["HF_REPORT_REPO"]

GH_TOKEN = os.environ["GH_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

WORK = Path("/tmp/root-audit")
SRC = WORK / "source"
OUT = WORK / "output"

OUT.mkdir(parents=True, exist_ok=True)

url = (
    f"https://x-access-token:{GH_TOKEN}"
    f"@github.com/{REPO}.git"
)

subprocess.run(
    ["git", "clone", "--branch", BRANCH,
     "--single-branch", url, str(SRC)],
    check=True
)

subprocess.run(
    ["git", "remote", "set-url", "origin",
     f"https://github.com/{REPO}.git"],
    cwd=SRC,
    check=True
)

KEEP = {
    "README.md",
    "AGENTS.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "vercel.json",
    ".gitignore",
    ".editorconfig",
    "Makefile"
}

RULES = {
    ".py": "backend/ o services/",
    ".js": "frontend/ o backend/",
    ".ts": "frontend/ o backend/",
    ".tsx": "frontend/",
    ".jsx": "frontend/",
    ".md": "docs/",
    ".yaml": "config/ o connections/",
    ".yml": "config/ o connections/",
    ".json": "config/ o schemas/",
    ".sh": "scripts/",
    ".sql": "database/",
    ".test.py": "tests/",
}

files = []
root_items = []

for path in SRC.iterdir():

    if path.name == ".git":
        continue

    root_items.append(path.name)

    if path.is_file():

        name = path.name
        suffix = path.suffix.lower()

        if name in KEEP:
            destination = "ROOT_KEEP"
            reason = "Archivo principal o configuración raíz"

        elif name.endswith(".test.py"):
            destination = "tests/"
            reason = "Archivo de prueba"

        elif suffix in RULES:
            destination = RULES[suffix]
            reason = "Clasificación por extensión; requiere validar contenido"

        else:
            destination = "MANUAL_REVIEW"
            reason = "No se puede determinar su responsabilidad"

        files.append({
            "file": name,
            "size": path.stat().st_size,
            "suggested_location": destination,
            "reason": reason
        })

    else:
        files.append({
            "file": path.name + "/",
            "type": "directory",
            "suggested_location": "EXISTING_DIRECTORY",
            "reason": "Revisar responsabilidad y contenido"
        })

report = {
    "repository": REPO,
    "branch": BRANCH,
    "commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=SRC, text=True
    ).strip(),
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "root": root_items,
    "inventory": files,
    "automatic_moves": False
}

(OUT / "root_structure.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False)
)

api_report = upload_folder(
    folder_path=str(OUT),
    repo_id=REPORT_REPO,
    repo_type="dataset",
    path_in_repo=f"root-audit/{report['commit']}",
    token=HF_TOKEN
)

print("ROOT AUDIT COMPLETED")
print("Files:", len(files))
print("Automatic moves: DISABLED")
