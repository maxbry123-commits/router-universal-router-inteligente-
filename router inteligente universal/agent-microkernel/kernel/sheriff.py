"""Sheriff: deterministic validator (never asks the LLM "is everything fine?"). Pydantic models + concrete checks."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

SECRET_RE = re.compile(r"(nvapi-[A-Za-z0-9_-]{20,}|gsk_[A-Za-z0-9]{20,}|csk-[a-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,})")


class Task(BaseModel):
    id: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=5, max_length=200)
    owner_agent: str
    priority: int = Field(ge=1, le=3)


class TaskList(BaseModel):
    tasks: list[Task] = Field(min_length=5)


class SheriffResult(BaseModel):
    passed: bool
    failures: list[str]
    evidence: list[dict[str, Any]]


def sha256(text: str | bytes) -> str:
    return hashlib.sha256(text.encode() if isinstance(text, str) else text).hexdigest()


def extract_code(text: str) -> str:
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip() + "\n"


def extract_js(text: str) -> str:
    m = re.search(r"```(?:js|javascript)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip() + "\n"


def extract_json(text: str) -> Any:
    body = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = body.find("{"), body.rfind("}")
    return json.loads(body[start:end + 1] if start >= 0 and end > start else body)


def run(checks: list[dict[str, Any]], output: str, workdir: Path, owners: set[str]) -> SheriffResult:
    fails: list[str] = []
    evidence = [{"kind": "output_sha256", "sha256": sha256(output), "chars": len(output)}]
    for c in checks:
        kind = c["kind"]
        if kind == "min_chars" and len(output) < c["value"]:
            fails.append(f"menos de {c['value']} caracteres")
        elif kind == "contains":
            for s in c["values"]:
                if s not in output:
                    fails.append(f"falta '{s}'")
        elif kind == "headings":
            for h in c["values"]:
                if not re.search(r"^\s*#{1,3}\s*" + re.escape(h) + r"\b", output, re.M | re.I):
                    fails.append(f"falta el encabezado '{h}'")
        elif kind == "no_secrets" and SECRET_RE.search(output):
            fails.append("el resultado contiene algo con forma de clave")
        elif kind == "python_ast":
            try:
                ast.parse(extract_code(output))
            except SyntaxError as exc:
                fails.append(f"Python inválido: {exc.msg} (línea {exc.lineno})")
        elif kind == "js_syntax":
            code = extract_js(output)
            workdir.mkdir(parents=True, exist_ok=True)
            target = workdir / c.get("file", "check.js")
            target.write_text(code, encoding="utf-8")
            try:
                p = subprocess.run(["node", "--check", str(target)], capture_output=True, text=True, timeout=25)
                evidence.append({"kind": "js_syntax", "exit": p.returncode, "file": target.name, "sha256": sha256(code)})
                if p.returncode != 0:
                    last = [ln for ln in (p.stderr or p.stdout).strip().splitlines() if ln.strip()]
                    fails.append("JavaScript inválido: " + (last[-1][:160] if last else "node --check falló"))
            except FileNotFoundError:
                fails.append("node no está disponible para validar JavaScript")
            except subprocess.TimeoutExpired:
                fails.append("la validación de JavaScript superó el tiempo")
        elif kind == "python_exec":
            code = extract_code(output)
            workdir.mkdir(parents=True, exist_ok=True)
            (workdir / c["module"]).write_text(code, encoding="utf-8")
            try:
                p = subprocess.run([sys.executable, "-c", c["test"]], cwd=workdir, capture_output=True, text=True, timeout=25)
                evidence.append({"kind": "exec", "exit": p.returncode, "file": c["module"], "sha256": sha256(code)})
                if p.returncode != 0:
                    last = (p.stderr or p.stdout).strip().splitlines()
                    fails.append("la prueba falló (exit=%d): %s" % (p.returncode, last[-1] if last else ""))
            except subprocess.TimeoutExpired:
                fails.append("la prueba superó el tiempo")
        elif kind == "task_list":
            try:
                tl = TaskList.model_validate(extract_json(output))
                ids = [t.id for t in tl.tasks]
                if len(set(ids)) != len(ids):
                    fails.append("ids de tarea repetidos")
                bad = sorted({t.owner_agent for t in tl.tasks} - owners)
                if bad:
                    fails.append(f"owner_agent desconocido: {bad}")
                evidence.append({"kind": "tasks", "count": len(tl.tasks)})
            except (ValidationError, ValueError) as exc:
                fails.append(f"lista de tareas inválida: {str(exc).splitlines()[0][:120]}")
    return SheriffResult(passed=not fails, failures=fails, evidence=evidence)
