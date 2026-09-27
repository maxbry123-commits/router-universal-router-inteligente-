"""SENTINELA ORQUESTADOR — adaptador T01-T08 sobre el LOOP común.

El núcleo está en 05-AGENTES/gobierno/sentinel_loop.py.
Este archivo solo adapta contratos de tareas, recopila evidencia real,
investiga, escribe una corrección y relanza el espejo.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
from urllib.parse import quote

import yaml

ROOT = pathlib.Path("chat router")
BASE = ROOT / "07-SENTINELAS"
GOBIERNO = ROOT / "05-AGENTES" / "gobierno"
sys.path.insert(0, str(GOBIERNO))

from sentinel_loop import (  # noqa: E402
    SentinelDSL,
    SentinelOrchestrator,
    SentinelResearchPlanner,
    SentinelSheriff,
)

CONTRATOS = BASE / "CONTRATOS.yaml"
REPLICAS = BASE / "REPLICAS.yaml"
ESTADO = BASE / "ESTADO-TAREAS.json"
INFORME = BASE / "informes/ORQUESTADOR.md"
TAREAS_DIR = ROOT / "06-ESPEJOS" / "tareas"
REPO = "maxbry123-commits/router-universal-router-inteligente-"
WF = "claude-code-espejos.yml"
MAX_INTENTOS = 3

RESEARCH_REPOS = {
    "T01": ["pytest-dev/pytest", "Aider-AI/aider"],
    "T02": ["pytest-dev/pytest"],
    "T03": ["diegosouzapw/OmniRoute"],
    "T04": ["anthropics/claude-code", "BerriAI/litellm"],
    "T05": ["pytest-dev/pytest"],
    "T06": ["NousResearch/hermes-agent", "openclaw/openclaw"],
    "T07": ["pytest-dev/pytest"],
    "T08": ["pytest-dev/pytest"],
}


def sh(cmd: list[str], timeout: int = 300, env: dict | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, (p.stdout + p.stderr)[-6000:]
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def ahora() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def espejos_activos() -> set[str]:
    rc, out = sh([
        "gh", "run", "list", "-R", REPO, "-w", WF,
        "-s", "in_progress", "--json", "databaseId", "-L", "10",
    ])
    activos: set[str] = set()
    if rc != 0:
        return activos
    for run in json.loads(out or "[]"):
        _, jobs = sh([
            "gh", "run", "view", str(run["databaseId"]),
            "-R", REPO, "--json", "jobs",
        ])
        for job in json.loads(jobs or "{}").get("jobs", []):
            name = job.get("name", "")
            if job.get("status") != "completed" and "(" in name:
                activos.add(name.split("(")[-1].rstrip(")"))
    return activos


def verificar(tid: str, c: dict, prohibido: list[str]) -> dict:
    scope = pathlib.Path(c["scope"])
    faltan = [
        f for f in c["required_files"]
        if not (scope / f).is_file() or (scope / f).stat().st_size == 0
    ]
    fugas = [
        p for p in prohibido
        if pathlib.Path(p).exists() and "chat router/chat router" in p
    ]
    rc, out = sh(
        ["bash", "-c", c["acceptance"]],
        env={**os.environ, "SIMULADO": "1"},
    )
    informe = ROOT / "06-ESPEJOS" / "informes" / f"{tid}.md"
    _, log = sh(["git", "log", "-1", "--format=%H %s", "--", c["scope"]])
    ev = {
        "faltan": faltan,
        "fugas": fugas,
        "pytest_exit": rc,
        "pytest_tail": out[-1600:],
        "informe": informe.is_file() and informe.stat().st_size > 0,
        "ultimo_commit": log.strip()[:160],
    }
    if not faltan and not fugas and rc == 0 and ev["informe"]:
        ev["veredicto"] = "PASS"
    elif faltan and len(faltan) == len(c["required_files"]):
        ev["veredicto"], ev["causa"] = "REVISE", "NO_ENTREGADO"
    elif faltan:
        ev["veredicto"], ev["causa"] = "REVISE", "ARCHIVOS_INCOMPLETOS"
    elif rc == 5:
        ev["veredicto"], ev["causa"] = "REVISE", "NO_TESTS"
    elif rc != 0:
        ev["veredicto"], ev["causa"] = "REVISE", "TESTS_FALLAN"
    else:
        ev["veredicto"], ev["causa"] = "REVISE", "SIN_INFORME"
    return ev


def spec_tarea(tid: str, c: dict, research_pool: list[str]):
    return SentinelDSL.parse({
        "sentinel_id": f"sentinela-{tid.lower()}",
        "objective": c["objective"],
        "repository": REPO,
        "report_path": str(INFORME),
        "priority_goals": [c["objective"]],
        "evidence_required": ["task_contract_observed", "task_pass"],
        "research_sources": research_pool,
        "max_attempts": MAX_INTENTOS,
        "max_research_sources": 20,
    })


def buscar_comunidad(tid: str, packet: dict) -> list[dict]:
    query = (
        packet.get("error_literal")
        or packet.get("failure")
        or "failure"
    ).replace("\n", " ")[:120]
    findings: list[dict] = []

    for repo in RESEARCH_REPOS.get(tid, []):
        rc, out = sh([
            "gh", "search", "issues", query,
            "--repo", repo, "--limit", "5",
            "--json", "title,url,state,updatedAt",
        ])
        if rc != 0:
            continue
        try:
            for item in json.loads(out or "[]"):
                item["source"] = f"GitHub:{repo}"
                findings.append(item)
                if len(findings) >= packet["max_sources"]:
                    return findings
        except json.JSONDecodeError:
            pass

    try:
        url = (
            "https://api.stackexchange.com/2.3/search/advanced"
            f"?site=stackoverflow&order=desc&sort=relevance&pagesize=5&q={quote(query)}"
        )
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read())
        for item in data.get("items", []):
            findings.append({
                "source": "StackOverflow",
                "title": item.get("title"),
                "url": item.get("link"),
            })
            if len(findings) >= packet["max_sources"]:
                break
    except Exception:
        pass

    return findings[:packet["max_sources"]]


def nvidia(prompt: str) -> str:
    for key_name in (
        "NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2",
        "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4",
    ):
        key = os.environ.get(key_name)
        if not key:
            continue
        for model in ("moonshotai/kimi-k3", "z-ai/glm-5.3", "z-ai/glm-5.3-flash"):
            body = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.1,
            }).encode()
            req = urllib.request.Request(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read())["choices"][0]["message"]["content"]
            except Exception:
                continue
    return ""


def investigar(tid: str, spec, ev: dict, intento: int) -> dict:
    error = ev.get("pytest_tail", "")[-1000:] or ev.get("causa", "")
    packet = SentinelResearchPlanner.build(
        spec,
        ev.get("causa", "UNKNOWN"),
        error,
        {"component": tid},
    )
    findings = buscar_comunidad(tid, packet)
    prompt = (
        f"Eres INVESTIGADOR del sentinela. No puedes declarar PASS. "
        f"Tarea={tid}. Objetivo={spec.objective}. Intento={intento}.\n"
        f"Veredicto determinista={ev['veredicto']} causa={ev.get('causa')} "
        f"faltan={ev['faltan']} pytest_exit={ev['pytest_exit']}\n"
        f"Error literal:\n{error}\n"
        f"Evidencia comunidad={json.dumps(findings, ensure_ascii=False)[:5000]}\n"
        "Responde máximo 12 líneas: CAUSA_RAIZ, EVIDENCIA, NO_REGENERAR, "
        "REPARAR, ACEPTACION."
    )
    return {
        "packet": packet,
        "fuentes": findings,
        "analisis": nvidia(prompt) or "sin respuesta del modelo; usar evidencia determinista",
    }


def ordenar(tid: str, intento: int, ev: dict, rp: dict) -> None:
    path = TAREAS_DIR / f"{tid}.md"
    if not path.is_file():
        return
    sheriff = SentinelSheriff()
    ok, motivo = sheriff.validate_write_paths([str(path)])
    if not ok:
        raise RuntimeError(motivo)
    text = (
        path.read_text(encoding="utf-8")
        + f"\n\n## CORRECCIÓN DEL SENTINELA (intento {intento}, {ahora()})\n"
        + f"Veredicto: {ev['veredicto']} · causa: {ev.get('causa')} · "
        + f"faltan: {ev['faltan']} · pytest exit: {ev['pytest_exit']}\n"
        + f"Fuentes consultadas: {len(rp['fuentes'])}.\n"
        + rp["analisis"]
        + "\nNo regeneres trabajo válido. Solo PASS con evidencia real y aceptación exit 0.\n"
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    cfg = yaml.safe_load(CONTRATOS.read_text(encoding="utf-8"))
    replicas = yaml.safe_load(REPLICAS.read_text(encoding="utf-8"))
    research_pool = list(replicas.get("research_pool", []))
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    head = sh(["git", "rev-parse", "HEAD"])[1].strip()
    activos = espejos_activos()
    loop = SentinelOrchestrator()

    relanzar: list[str] = []
    lineas = [
        f"# SENTINELA ORQUESTADOR — {ahora()} · observed_sha {head[:10]}",
        "",
        "| Tarea | Estado | Causa | Intento | Evidencia |",
        "|---|---|---|---|---|",
    ]

    for tid, c in cfg["tareas"].items():
        st = estado.get(tid, {"attempt": 0})
        spec = spec_tarea(tid, c, research_pool)

        if tid in activos:
            st.update({"status": "ACTIVE", "last_sha": head, "next_action": "esperar ejecutor"})
        else:
            ev = verificar(tid, c, cfg.get("prohibido_global", []))
            common_evidence = {
                "observed_sha": head,
                "current_sha": head,
                "executor_active": False,
                "workflow_false_green": False,
                "unauthorized_change": bool(ev["fugas"]),
                "failure_class": ev.get("causa", ""),
                "objective_evidence": {
                    "task_contract_observed": True,
                    "task_pass": ev["veredicto"] == "PASS",
                },
            }
            decision = loop.next_action(spec, st, common_evidence)
            st.update({"last_sha": head, "evidence": ev})

            if decision["state"] == "PASS":
                st.update({
                    "status": "PASS",
                    "next_action": "ninguna",
                    "last_failure": "",
                })
            elif st.get("attempt", 0) >= MAX_INTENTOS:
                st.update({
                    "status": "BLOCKED",
                    "next_action": "revisión de Opus/Director",
                    "last_failure": ev.get("causa"),
                })
            else:
                st["attempt"] = st.get("attempt", 0) + 1
                rp = investigar(tid, spec, ev, st["attempt"])
                ordenar(tid, st["attempt"], ev, rp)
                st.update({
                    "status": decision["state"],
                    "last_failure": ev.get("causa"),
                    "research_packet": rp["packet"],
                    "research_findings": rp["fuentes"],
                    "next_action": "espejo relanzado",
                })
                relanzar.append(tid)

        estado[tid] = st
        ev = st.get("evidence", {})
        lineas.append(
            f"| {tid} | {st['status']} | {st.get('last_failure', '')} | "
            f"{st.get('attempt', 0)} | faltan {len(ev.get('faltan', []))} "
            f"· pytest {ev.get('pytest_exit', '-')} |"
        )

    ESTADO.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    INFORME.parent.mkdir(parents=True, exist_ok=True)
    INFORME.write_text(
        "\n".join(lineas)
        + f"\n\nRelanzados: {', '.join(relanzar) or 'ninguno'}\n",
        encoding="utf-8",
    )
    print("\n".join(lineas))

    if relanzar:
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as g:
            g.write("relanzar=" + ",".join(relanzar) + "\n")


if __name__ == "__main__":
    main()
