"""Download engine for the agent donors (deterministic, no LLM): shallow/sparse clones of the agents the Director named, copying only small text/code files
(<= 150 KB each, <= 2 MB per donor) into agents-yaiwes/donors/<name>/ and writing donors/MANIFEST.json (url, commit, files, bytes, status).
Donors: the 4 Meta agents (Muse Code SDK, Muse Glimmer agent loop, MetaCua, CUA + MCP) and the two frameworks (SmolAgents, PocketFlow)."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # agents-yaiwes
OUT = HERE / "donors"
DONORS = {
    "muse-code-sdk": ("https://github.com/meta-models/muse-code-sdk", None),
    "meta-oss-cookbook-agentic-fundamentals": ("https://github.com/meta-models/meta-oss-cookbook", ["agentic-fundamentals"]),
    "meta-model-cookbook-12-computer-use": ("https://github.com/meta-models/meta-model-cookbook", ["03_use_cases/12_computer_use"]),
    "meta-model-cookbook-13-macos-cua": ("https://github.com/meta-models/meta-model-cookbook", ["03_use_cases/13_macos_cua"]),
    "smolagents": ("https://github.com/huggingface/smolagents", ["src/smolagents", "README.md"]),
    "pocketflow": ("https://github.com/The-Pocket/PocketFlow", ["pocketflow", "README.md"]),
}
EXT = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".ts", ".js", ".sh"}
MAX_FILE, MAX_TOTAL = 150_000, 2_000_000


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def fetch(name: str, url: str, sparse: list[str] | None) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp) / "r"
        p = run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", url, str(tmpd)])
        if p.returncode != 0:
            return {"url": url, "status": "NO_DISPONIBLE", "error": (p.stderr or p.stdout).strip().splitlines()[-1][:160] if (p.stderr or p.stdout).strip() else "clone falló"}
        if sparse:
            run(["git", "sparse-checkout", "set", "--no-cone", *sparse], cwd=tmpd)
        else:
            run(["git", "sparse-checkout", "disable"], cwd=tmpd)
        run(["git", "checkout"], cwd=tmpd)
        commit = run(["git", "rev-parse", "HEAD"], cwd=tmpd).stdout.strip()
        dest = OUT / name
        if dest.exists():
            shutil.rmtree(dest)
        total, count, skipped = 0, 0, 0
        for f in sorted(tmpd.rglob("*")):
            if not f.is_file() or ".git" in f.relative_to(tmpd).parts or f.suffix.lower() not in EXT:
                continue
            size = f.stat().st_size
            if size > MAX_FILE or total + size > MAX_TOTAL:
                skipped += 1
                continue
            target = dest / f.relative_to(tmpd)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            total, count = total + size, count + 1
        return {"url": url, "status": "OK" if count else "SIN_ARCHIVOS", "commit": commit, "files": count, "bytes": total, "skipped_big": skipped, "sparse": sparse}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, (url, sparse) in DONORS.items():
        try:
            manifest[name] = fetch(name, url, sparse)
        except Exception as exc:  # noqa: BLE001
            manifest[name] = {"url": url, "status": "ERROR", "error": f"{type(exc).__name__}: {str(exc)[:120]}"}
        print(f"::notice title=RIU_DONOR_{name}::{manifest[name].get('status')} files={manifest[name].get('files', '-')} commit={str(manifest[name].get('commit', '-'))[:10]} {manifest[name].get('error', '')}")
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
