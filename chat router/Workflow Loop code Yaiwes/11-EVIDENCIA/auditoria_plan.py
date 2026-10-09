"""Coteja el plan enlazado y las referencias visuales sin atribuirles ejecución."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "chat router/Workflow Loop code Yaiwes/01-PLAN"
CATALOG = PLAN / "CATALOGO-REFERENCIAS-UI.json"
EXTRA_CATALOG = PLAN / "CATALOGO-ANEXOS-VISUALES.json"
OUTPUT = PLAN / "AUDITORIA-4-PASADAS.json"
SOURCE = "aa8fed0631913783c77d3b9ad3fcca62e1978c11"
SKILL_SOURCE = "cf6c5068b43800954cf9c33f878aeb87fea2501f"
OLD_SKILLS = "📂 Skills Maxbry UI fromtend/"
NEW_SKILLS = "chat router/Workflow Loop code Yaiwes/01-PLAN/SKILLS-MAXBRY-UI/"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def entries(revision: str, path: str | None = None) -> list[tuple[str, str]]:
    command = ["ls-tree", "-r", "-z", revision]
    if path:
        command += ["--", path]
    rows = git(*command).split(b"\0")
    return [
        (name.decode("utf-8"), info.split()[2].decode("ascii"))
        for row in rows if row
        for info, name in [row.split(b"\t", 1)]
    ]


def index_entries() -> list[tuple[str, str]]:
    return [
        (name.decode("utf-8"), info.split()[1].decode("ascii"))
        for row in git("ls-files", "--stage", "-z").split(b"\0") if row
        for info, name in [row.split(b"\t", 1)]
    ]


def structure_for(path: str, data: bytes) -> str:
    suffix = Path(path).suffix
    if suffix == ".zip":
        with zipfile.ZipFile(ROOT / path) as archive:
            bad = archive.testzip()
            return "ZIP_INTEGRITY_VALID" if bad is None else f"🚩 PENDIENTE: ZIP_BAD_MEMBER:{bad}"
    if suffix in {".py", ".json", ".yaml", ".yml", ".sh", ".js", ".mjs", ".html", ".tsx"}:
        text = data.decode("utf-8")
        if suffix == ".py":
            ast.parse(text, filename=path)
            return "PYTHON_SYNTAX_VALID"
        if suffix == ".json":
            json.loads(text)
            return "JSON_SYNTAX_VALID"
        if suffix in {".yaml", ".yml"}:
            yaml.safe_load(text)
            return "YAML_SYNTAX_VALID"
        if suffix in {".sh", ".js", ".mjs"}:
            cmd = ["bash", "-n", str(ROOT / path)] if suffix == ".sh" else ["node", "--check", str(ROOT / path)]
            result = subprocess.run(cmd, capture_output=True, check=False)
            return "SYNTAX_VALID" if result.returncode == 0 else "🚩 PENDIENTE: SYNTAX_INVALID"
        if suffix == ".html":
            parser = HTMLParser()
            parser.feed(text)
            parser.close()
            return "HTML_TOKENIZED_NOT_BROWSER_VALIDATED"
        return "🚩 PENDIENTE: TSX_NOT_PARSED"
    if suffix in {".md", ".txt", ".css"}:
        data.decode("utf-8")
        return "TEXT_UTF8_VALID"
    return "🚩 PENDIENTE: STRUCTURE_NOT_PARSED"


def audit_document(path: str, blob: str, preserved: dict[str, list[str]]) -> dict:
    data = git("cat-file", "blob", blob)
    locations = preserved.get(blob, [])
    content = data.decode("utf-8")
    headings = re.findall(r"^#{1,4}\s+(.+)$", content, re.MULTILINE)
    kind = "PYTHON_REFERENCE" if path.endswith(".py") else "DSL" if path.endswith(".yaml") else "INPUT" if path.endswith(".txt") else "DOCUMENT"
    current = path if path in locations else next((name for name in locations if name.startswith("chat router/Workflow Loop code Yaiwes/01-PLAN/")), locations[0] if locations else None)
    structure = structure_for(current or path, data)
    return {
        "source": path,
        "current": current,
        "source_blob": blob,
        "sha256": sha256(data),
        "bytes": len(data),
        "kind": kind,
        "passes": {
            "1_provenance": "PRESERVED_IN_BRANCH" if current and sha256((ROOT / current).read_bytes()) == sha256(data) else "🚩 PENDIENTE: SOURCE_BLOB_MISSING",
            "2_structure": structure,
            "3_wiring": "🚩 PENDIENTE: RUNTIME_WIRING_NOT_DEMONSTRATED",
            "4_evidence": "🚩 PENDIENTE: EXECUTION_AND_READBACK_PER_REQUIREMENT",
        },
        "heading_count": len(headings),
        "headings_sample": headings[:3],
    }


def audit_skill(path: str, blob: str, indexed: dict[str, str]) -> dict:
    current = NEW_SKILLS + path.removeprefix(OLD_SKILLS)
    data = (ROOT / current).read_bytes()
    original = git("cat-file", "blob", blob)
    intact = indexed.get(current) == blob and data == original
    return {
        "source": path, "current": current, "source_blob": blob,
        "sha256": sha256(data), "bytes": len(data),
        "kind": Path(current).suffix.lower().lstrip(".").upper() or "UNKNOWN",
        "passes": {
            "1_provenance": "PRESERVED_IN_BRANCH" if intact else "🚩 PENDIENTE: SOURCE_CHANGED",
            "2_structure": structure_for(current, data),
            "3_wiring": "🚩 PENDIENTE: RUNTIME_WIRING_NOT_DEMONSTRATED",
            "4_evidence": "🚩 PENDIENTE: COMPONENT_TEST_AND_READBACK",
        },
    }


def audit_image(item: dict) -> dict:
    path = ROOT / item["file"]
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or sha256(data) != item["sha256"] or len(data) != item["bytes"]:
        raise ValueError(f"IMAGE_MISMATCH:{item['id']}")
    return {
        "id": item["id"],
        "file": item["file"],
        "sha256": item["sha256"],
        "bytes": item["bytes"],
        "width": item["width"],
        "height": item["height"],
        "duplicate_of": item["duplicate_of"],
        "proposed_function": item["function"],
        "source": item.get("original", item.get("group", "SOURCE_UNSPECIFIED")),
        "passes": {
            "1_provenance": "CATALOG_HASH_VERIFIED",
            "2_structure": "PNG_HEADER_AND_DIMENSIONS_VERIFIED; ROLE_CATALOG_ONLY",
            "3_wiring": "🚩 PENDIENTE: BACKEND_AND_FRONTEND_NOT_CONNECTED",
            "4_evidence": "🚩 PENDIENTE: VISUAL_AND_SECRET_REVIEW",
        },
    }


def build() -> dict:
    original = entries(SOURCE, "chat router/Workflow Loop code Yaiwes/01-PLAN")
    indexed = dict(index_entries())
    preserved: dict[str, list[str]] = {}
    for path, blob in indexed.items():
        preserved.setdefault(blob, []).append(path)
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    extra = json.loads(EXTRA_CATALOG.read_text(encoding="utf-8"))
    documents = [audit_document(path, blob, preserved) for path, blob in original]
    skill_sources = [(path, blob) for path, blob in entries(SKILL_SOURCE, OLD_SKILLS)]
    skills = [audit_skill(path, blob, indexed) for path, blob in skill_sources]
    images = [audit_image(item) for item in catalog["items"] + extra["items"]]
    if (len(documents) != 30 or len(skills) != 82 or len(images) != 82
            or catalog["count"] != 65 or extra["count"] != 17):
        raise ValueError("SOURCE_INVENTORY_CHANGED")
    duplicates = {digest: count for digest, count in Counter(item["sha256"] for item in documents).items() if count > 1}
    if len(duplicates) != 2:
        raise ValueError("SOURCE_DUPLICATES_CHANGED")
    return {
        "schema": "yaiwes.plan-audit/v2",
        "commit": SOURCE,
        "four_passes": ["source/hash", "structure/contract", "runtime wiring", "execution/read-back"],
        "summary": {
            "documents": len(documents), "distinct_document_content": len({item["sha256"] for item in documents}),
            "document_duplicates": duplicates, "skills": len(skills), "images": len(images),
            "documents_preserved": sum(item["passes"]["1_provenance"] == "PRESERVED_IN_BRANCH" for item in documents),
            "skills_preserved": sum(item["passes"]["1_provenance"] == "PRESERVED_IN_BRANCH" for item in skills),
            "images_hash_verified": len(images),
            "runtime_verified_by_this_audit": 0, "visually_verified_by_this_audit": 0,
        },
        "documents": documents,
        "skills": skills,
        "images": images,
    }


def main() -> None:
    report = build()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if json.loads(OUTPUT.read_text(encoding="utf-8")) != report:
        raise OSError("AUDIT_READBACK_FAILED")
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
