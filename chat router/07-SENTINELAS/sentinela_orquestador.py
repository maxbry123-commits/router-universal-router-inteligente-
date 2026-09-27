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
    SentinelContextBuilder,
    SentinelDSL,
    SentinelOrchestrator,
    SentinelResearchPlanner,
    SentinelSheriff,
    SentinelSupervisor,
)

CONTRATOS = BASE / "CONTRATOS.yaml"
REPLICAS = BASE / "REPLICAS.yaml"
FOCUS = BASE / "FOCUS.yaml"
ESTADO = BASE / "ESTADO-TAREAS.json"
INFORME = BASE / "informes/ORQUESTADOR.md"
TAREAS_DIR = ROOT / "06-ESPEJOS" / "tareas"
REPO = "maxbry123-commits/router-universal-router-inteligente-"
WF = "claude-code-espejos.yml"
MAX_INTENTOS = 5
DETERMINISTIC_FAILURES = {
    "NO_ENTREGADO",
    "ARCHIVOS_INCOMPLETOS",
    "NO_TESTS",
    "SIN_INFORME",
}

RESEARCH_REPOS = {
    "T01": ["pytest-dev/pytest", "Aider-AI/aider"],
    "T02": ["pytest-dev/pytest"],
    "T03": ["diegosouzapw/OmniRoute"],
    "T04": [
        "anthropics/claude-code",
        "BerriAI/litellm",
        "codeaashu/free-claude-code",
        "claude-server/claude-nim",
        "deepseek-ai/deepseek-harness",
    ],
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


def espejos_activos() -> dict[str, dict]:
    """Devuelve ejecutores activos con run/job/step para supervisión real."""
    rc, out = sh([
        "gh", "run", "list", "-R", REPO, "-w", WF,
        "-s", "in_progress", "--json", "databaseId", "-L", "10",
    ])
    activos: dict[str, dict] = {}
    if rc != 0:
        return activos
    now = dt.datetime.now(dt.timezone.utc)
    for run in json.loads(out or "[]"):
        run_id = run.get("databaseId")
        _, jobs = sh([
            "gh", "run", "view", str(run_id),
            "-R", REPO, "--json", "jobs",
        ])
        for job in json.loads(jobs or "{}").get("jobs", []):
            name = job.get("name", "")
            if job.get("status") == "completed" or "(" not in name:
                continue
            tid = name.split("(")[-1].rstrip(")")
            steps = job.get("steps", [])
            active_step = next(
                (s for s in steps if s.get("status") == "in_progress"),
                {},
            )
            age = 0
            started = active_step.get("startedAt") or job.get("startedAt")
            if started:
                try:
                    stamp = dt.datetime.fromisoformat(str(started).replace("Z", "+00:00"))
                    age = max(0, int((now - stamp).total_seconds() // 60))
                except ValueError:
                    age = 0
            activos[tid] = {
                "executor_active": True,
                "run_id": run_id,
                "job_id": job.get("databaseId"),
                "active_step": active_step.get("name") or "ejecutor activo",
                "active_step_age_minutes": age,
            }
    return activos


def mirror_changed_files(tid: str) -> list[str]:
    """Inspecciona una rama REVISE sin mezclarla con el worktree actual."""
    ref = f"refs/remotes/origin/mirror/{tid}"
    rc, _ = sh(["git", "ls-remote", "--exit-code", "--heads", "origin", f"mirror/{tid}"])
    if rc != 0:
        return []
    rc, _ = sh([
        "git", "fetch", "-q", "origin",
        f"refs/heads/mirror/{tid}:{ref}",
    ])
    if rc != 0:
        return []
    rc, out = sh(["git", "diff", "--name-only", f"HEAD...{ref}"])
    return [line.strip() for line in out.splitlines() if line.strip()] if rc == 0 else []


def verificar(tid: str, c: dict, prohibido: list[str]) -> dict:
    scope = pathlib.Path(c["scope"])
    faltan = [
        f for f in c["required_files"]
        if not (scope / f).is_file() or (
            (scope / f).name != "__init__.py" and (scope / f).stat().st_size == 0
        )
    ]
    fugas = [
        p for p in prohibido
        if pathlib.Path(p).exists() and "chat router/chat router" in p
    ]

    changed = mirror_changed_files(tid)
    task_spec = spec_tarea(tid, c, [])
    sheriff_ok, sheriff_reason = SentinelSheriff().validate_executor_paths(
        task_spec, changed
    )
    scope_escape = None if sheriff_ok else sheriff_reason

    rc, out = sh(
        ["bash", "-c", c["acceptance"]],
        env={**os.environ, "SIMULADO": "1"},
    )

    objective_failures: list[str] = []
    if not faltan:
        for check in c.get("objective_checks", []):
            crc, cout = sh(
                ["bash", "-c", check],
                env={**os.environ, "SIMULADO": "1"},
            )
            if crc != 0:
                objective_failures.append(
                    f"{check} :: {cout[-300:].strip()}"
                )

    informe = ROOT / "06-ESPEJOS" / "informes" / f"{tid}.md"
    _, log = sh(["git", "log", "-1", "--format=%H %ct %s", "--", c["scope"]])
    _, report_log = sh(["git", "log", "-1", "--format=%ct", "--", str(informe)])
    scope_parts = log.strip().split(maxsplit=2)
    scope_ts = int(scope_parts[1]) if len(scope_parts) >= 2 and scope_parts[1].isdigit() else 0
    report_ts = int(report_log.strip()) if report_log.strip().isdigit() else 0
    informe_ok = informe.is_file() and informe.stat().st_size > 0
    stale_report = bool(informe_ok and scope_ts and report_ts < scope_ts)

    ev = {
        "faltan": faltan,
        "fugas": fugas,
        "changed_files": changed,
        "scope_escape": scope_escape,
        "objective_failures": objective_failures,
        "objective_drift": bool(objective_failures),
        "pytest_exit": rc,
        "pytest_tail": out[-1600:],
        "informe": informe_ok,
        "stale_report": stale_report,
        "ultimo_commit": log.strip()[:200],
    }

    if scope_escape:
        ev["veredicto"], ev["causa"] = "REVISE", "SCOPE_ESCAPE"
    elif objective_failures:
        ev["veredicto"], ev["causa"] = "REVISE", "OBJECTIVE_DRIFT"
    elif stale_report:
        ev["veredicto"], ev["causa"] = "REVISE", "STALE_REPORT"
    elif not faltan and not fugas and rc == 0 and informe_ok:
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
        "evidence_required": [
            "task_contract_observed",
            "scope_clean",
            "objective_checks_pass",
            "report_fresh",
            "task_pass",
        ],
        "research_sources": research_pool,
        "task_scope": c["scope"],
        "required_files": c["required_files"],
        "acceptance": c["acceptance"],
        "objective_checks": c.get("objective_checks", []),
        "max_attempts": MAX_INTENTOS,
        "max_research_sources": 20,
        "max_stall_minutes": int(c.get("max_stall_minutes", 30)),
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


def diagnostico_determinista(tid: str, spec, ev: dict, intento: int) -> dict:
    """Evita gastar LLM/web cuando la causa ya está demostrada por evidencia local."""
    causa = ev.get("causa", "UNKNOWN")
    faltan = ev.get("faltan", [])
    packet = SentinelResearchPlanner.build(
        spec,
        causa,
        ev.get("pytest_tail", "")[-1000:],
        {"component": tid},
    )
    if causa == "NO_ENTREGADO":
        repair = (
            f"Crear únicamente los archivos faltantes declarados por el contrato: {faltan}. "
            "Seguir la tarea literal y ejecutar la aceptación real."
        )
        no_regen = "ninguno; no hay entrega válida en main"
    elif causa == "ARCHIVOS_INCOMPLETOS":
        repair = (
            f"Conservar archivos existentes y completar solo los faltantes: {faltan}. "
            "Después ejecutar la aceptación real."
        )
        no_regen = "todos los archivos existentes y no vacíos"
    elif causa == "NO_TESTS":
        repair = "Crear/corregir únicamente tests del alcance hasta que pytest descubra tests reales."
        no_regen = "código existente que no esté implicado en el fallo"
    else:
        repair = "Completar únicamente el informe con salida real de la aceptación; no regenerar código válido."
        no_regen = "todo el código existente"
    analysis = (
        f"CAUSA_RAIZ: {causa} demostrada por evidencia determinista.\n"
        f"EVIDENCIA: faltan={faltan} pytest_exit={ev.get('pytest_exit')}.\n"
        f"NO_REGENERAR: {no_regen}.\n"
        f"REPARAR: {repair}\n"
        f"ACEPTACION: {spec.objective} — ejecutar el comando contractual y exigir exit 0."
    )
    return {"packet": packet, "fuentes": [], "analisis": analysis}


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
        "Identifica también GAPS de conocimiento/protocolo. "
        "Responde máximo 12 líneas: CAUSA_RAIZ, EVIDENCIA, GAPS, "
        "NO_REGENERAR, REPARAR, ACEPTACION."
    )
    return {
        "packet": packet,
        "fuentes": findings,
        "analisis": nvidia(prompt) or "sin respuesta del modelo; usar evidencia determinista",
    }


def crear_contexto(tid: str, spec, ev: dict, rp: dict) -> None:
    path = TAREAS_DIR / f"{tid}-SENTINEL-CONTEXT.md"
    sheriff = SentinelSheriff()
    ok, motivo = sheriff.validate_write_paths([str(path)])
    if not ok:
        raise RuntimeError(motivo)
    path.write_text(
        SentinelContextBuilder.build(spec, tid, ev, rp),
        encoding="utf-8",
    )


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
    focus_cfg = yaml.safe_load(FOCUS.read_text(encoding="utf-8"))
    focus_tid = str(focus_cfg.get("active_task", "")).strip()
    if focus_tid not in cfg.get("tareas", {}):
        raise SystemExit(f"focus inválido: {focus_tid}")
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

        if tid != focus_tid:
            st.update({
                "status": st.get("status", "WAITING_FOCUS"),
                "next_action": f"esperar; foco actual {focus_tid}",
            })
            estado[tid] = st
            ev = st.get("evidence", {})
            lineas.append(
                f"| {tid} | WAITING_FOCUS | foco={focus_tid} | "
                f"{st.get('attempt', 0)} | faltan {len(ev.get('faltan', []))} "
                f"· pytest {ev.get('pytest_exit', '-')} |"
            )
            continue

        if tid in activos:
            runtime = activos[tid]
            supervision = SentinelSupervisor().inspect(spec, runtime)
            st.update({
                "status": "ACTIVE",
                "last_sha": head,
                "runtime": runtime,
                "supervision": supervision,
                "next_action": f"vigilar: {supervision['reason']}",
            })
            if supervision["action"] in {"BLOCK", "INTERVENE", "RESEARCH"}:
                run_id = runtime.get("run_id")
                if run_id:
                    sh(["gh", "run", "cancel", str(run_id), "-R", REPO], timeout=30)
                st.update({
                    "status": "RESEARCH",
                    "last_failure": supervision["reason"],
                    "next_action": "ejecutor detenido; investigar y recontextualizar",
                })
        else:
            ev = verificar(tid, c, cfg.get("prohibido_global", []))
            common_evidence = {
                "observed_sha": head,
                "current_sha": head,
                "executor_active": False,
                "workflow_false_green": False,
                "unauthorized_change": bool(ev["fugas"]),
                "scope_escape": bool(ev.get("scope_escape")),
                "objective_drift": bool(ev.get("objective_drift")),
                "stale_report": bool(ev.get("stale_report")),
                "failure_class": ev.get("causa", ""),
                "objective_evidence": {
                    "task_contract_observed": True,
                    "scope_clean": not bool(ev.get("scope_escape")),
                    "objective_checks_pass": not bool(ev.get("objective_failures")),
                    "report_fresh": not bool(ev.get("stale_report")),
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
                previous_attempts = st.get("attempt", 0)
                st["attempt"] = previous_attempts + 1
                # Primer fallo puramente estructural puede resolverse directo.
                # Si el agente YA falló una vez, existe un GAP: investigar antes
                # de volver a empujarlo, aunque la causa sea determinista.
                must_research = (
                    previous_attempts >= 1
                    or ev.get("causa") not in DETERMINISTIC_FAILURES
                    or bool(ev.get("objective_drift"))
                    or bool(ev.get("scope_escape"))
                )
                if must_research:
                    rp = investigar(tid, spec, ev, st["attempt"])
                else:
                    rp = diagnostico_determinista(tid, spec, ev, st["attempt"])
                crear_contexto(tid, spec, ev, rp)
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
        + f"\n\nFoco: {focus_tid}\nRelanzados: {', '.join(relanzar) or 'ninguno'}\n",
        encoding="utf-8",
    )
    print("\n".join(lineas))

    if relanzar:
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as g:
            g.write("relanzar=" + ",".join(relanzar) + "\n")


if __name__ == "__main__":
    main()
