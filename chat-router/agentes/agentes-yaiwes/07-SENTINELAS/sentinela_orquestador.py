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
    "T03A": ["diegosouzapw/OmniRoute", "WiseLibs/better-sqlite3"],
    "T03B": ["diegosouzapw/OmniRoute", "WiseLibs/better-sqlite3"],
    "T03C": ["diegosouzapw/OmniRoute", "WiseLibs/better-sqlite3"],
    "T03C1": ["diegosouzapw/OmniRoute", "WiseLibs/better-sqlite3"],
    "T03C2": ["diegosouzapw/OmniRoute", "WiseLibs/better-sqlite3"],
    "T04": [
        "anthropics/claude-code",
        "BerriAI/litellm",
        "codeaashu/free-claude-code",
        "claude-server/claude-nim",
        "deepseek-ai/deepseek-harness",
    ],
    "T05": [
        "fastapi/fastapi",
        "karpathy/llm-council",
        "pytest-dev/pytest",
    ],
    "T06": [
        "maxbry123-commits/hermes-agent",
        "maxbry123-commits/openclaw",
        "NousResearch/hermes-agent",
        "openclaw/openclaw",
    ],
    "T07": [
        "HuskyInSalt/CRAG",
        "anthonywchen/RARR",
        "google-deepmind/long-form-factuality",
        "amazon-science/RAGChecker",
        "pytest-dev/pytest",
    ],
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
    try:
        runs = json.loads(out or "[]")
    except json.JSONDecodeError:
        return activos
    for run in runs:
        run_id = run.get("databaseId")
        jobs_rc, jobs = sh([
            "gh", "run", "view", str(run_id),
            "-R", REPO, "--json", "jobs",
        ], timeout=20)
        if jobs_rc != 0:
            continue
        try:
            job_items = json.loads(jobs or "{}").get("jobs", [])
        except json.JSONDecodeError:
            continue
        for job in job_items:
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


def mirror_branch(tid: str) -> str:
    return {
        "T03A": "mirror/T03",
        "T03B": "mirror/T03-B",
        "T03C": "mirror/T03-C",
        "T03C1": "mirror/T03-C1",
        "T03C2": "mirror/T03-C2",
    }.get(tid, f"mirror/{tid}")


def mirror_changed_files(tid: str) -> list[str]:
    """Inspecciona una rama REVISE sin mezclarla con el worktree actual."""
    branch = mirror_branch(tid)
    ref = f"refs/remotes/origin/{branch}"
    rc, _ = sh(["git", "ls-remote", "--exit-code", "--heads", "origin", branch], timeout=20)
    if rc != 0:
        return []
    rc, _ = sh([
        "git", "fetch", "-q", "origin",
        f"refs/heads/{branch}:{ref}",
    ], timeout=20)
    if rc != 0:
        return []
    rc, out = sh(["git", "diff", "--name-only", f"HEAD...{ref}"])
    if rc != 0:
        return []

    # El workflow genera el informe fuera del scope de la tarea.
    # No es una escritura del agente y no debe contarse como SCOPE_ESCAPE.
    generated_report = f"chat router/06-ESPEJOS/informes/{tid}.md"
    return [
        line.strip()
        for line in out.splitlines()
        if line.strip() and line.strip() != generated_report
    ]


def auditar_ultimo_ejecutor(tid: str) -> dict:
    """Lee el último job completado de la tarea y conserva anomalías recuperadas."""
    rc, out = sh([
        "gh", "run", "list", "-R", REPO, "-w", WF,
        "-s", "completed", "--json", "databaseId,conclusion,createdAt", "-L", "4",
    ], timeout=20)
    if rc != 0:
        return {}
    for run in json.loads(out or "[]"):
        run_id = run.get("databaseId")
        _, jobs = sh([
            "gh", "run", "view", str(run_id),
            "-R", REPO, "--json", "jobs",
        ])
        for job in json.loads(jobs or "{}").get("jobs", []):
            if job.get("name") != f"espejo ({tid})":
                continue
            job_id = job.get("databaseId")
            lrc, log = sh([
                "gh", "run", "view", str(run_id), "-R", REPO,
                "--job", str(job_id), "--log",
            ], timeout=30)
            if lrc != 0:
                log = ""
            path_escapes = log.count("FAIL_PATH_ESCAPE")
            no_tests = "pytest exit=5" in log or "acceptance exit: 5" in log
            agent_ok_acceptance_bad = (
                "aider terminó rc=0" in log
                and ("VEREDICTO REVISE" in log or "acceptance exit: 0" not in log)
            )
            return {
                "run_id": run_id,
                "job_id": job_id,
                "conclusion": run.get("conclusion"),
                "path_escape_count": path_escapes,
                "no_tests": no_tests,
                "false_green_agent": agent_ok_acceptance_bad,
                "recovered_deviation": bool(path_escapes),
            }
    return {}


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
    informe = ROOT / "06-ESPEJOS" / "informes" / f"{tid}.md"
    informe_text = informe.read_text(encoding="utf-8") if informe.is_file() else ""
    path_escape_count = informe_text.count("FAIL_PATH_ESCAPE")
    executor_audit = {
        "path_escape_count": path_escape_count,
        "recovered_deviation": path_escape_count > 0,
        "source": "informe",
    }
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
        "executor_audit": executor_audit,
        "recovered_deviation": bool(executor_audit.get("recovered_deviation")),
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
    """Investiga el objetivo real: repos oficiales primero, luego issues/comunidad."""
    failure = str(packet.get("failure", "")).strip()
    objective = str(packet.get("objective", "")).strip()
    literal = str(packet.get("error_literal", "")).replace("\n", " ").strip()
    findings: list[dict] = []

    repos = RESEARCH_REPOS.get(tid, [])
    for repo in repos:
        findings.append({
            "source": "Repositorio oficial/upstream",
            "title": repo,
            "url": f"https://github.com/{repo}",
        })
        if len(findings) >= packet["max_sources"]:
            return findings

    queries = []
    if objective:
        queries.append(objective[:120])
    if literal:
        queries.append(literal[:120])
    if failure:
        queries.append(failure[:120])

    seen: set[str] = set()
    for repo in repos:
        for query in queries:
            rc, out = sh([
                "gh", "search", "issues", query,
                "--repo", repo, "--limit", "3",
                "--json", "title,url,state,updatedAt",
            ])
            if rc != 0:
                continue
            try:
                for item in json.loads(out or "[]"):
                    url = item.get("url", "")
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    item["source"] = f"GitHub:{repo}"
                    findings.append(item)
                    if len(findings) >= packet["max_sources"]:
                        return findings
            except json.JSONDecodeError:
                pass

    # Comunidad independiente: usar objetivo/error, nunca una etiqueta interna
    # como OBJECTIVE_DRIFT como consulta principal.
    query = (literal or objective or failure or "software integration")[:120]
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
    raw_focus = focus_cfg.get("active_tasks")
    if isinstance(raw_focus, list) and raw_focus:
        focus_tids = [str(t).strip() for t in raw_focus if str(t).strip()]
    else:
        focus_tids = [str(focus_cfg.get("active_task", "")).strip()]
    invalid = [t for t in focus_tids if t not in cfg.get("tareas", {})]
    if invalid:
        raise SystemExit(f"focus inválido: {invalid}")
    focus_label = ",".join(focus_tids)
    research_pool = list(replicas.get("research_pool", []))
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    head = sh(["git", "rev-parse", "HEAD"])[1].strip()
    activos = espejos_activos()

    def related_to_focus(active_tid: str) -> bool:
        if active_tid in focus_tids:
            return True
        # Si el foco es el padre T03, sus microtareas T03A/T03B/T03C*
        # no deben bloquear la verificación final del padre.
        return any(
            focus == "T03" and active_tid.startswith("T03")
            for focus in focus_tids
        )

    foreign_actives = sorted(t for t in activos if not related_to_focus(t))
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

        if tid not in focus_tids:
            st.update({
                "status": st.get("status", "WAITING_FOCUS"),
                "next_action": f"esperar; foco actual {focus_label}",
            })
            estado[tid] = st
            ev = st.get("evidence", {})
            lineas.append(
                f"| {tid} | WAITING_FOCUS | foco={focus_label} | "
                f"{st.get('attempt', 0)} | faltan {len(ev.get('faltan', []))} "
                f"· pytest {ev.get('pytest_exit', '-')} |"
            )
            continue

        if tid not in activos and foreign_actives:
            st.update({
                "status": "WAITING_EXECUTOR",
                "last_sha": head,
                "next_action": (
                    "esperar ejecutor activo: " + ",".join(foreign_actives)
                    + "; no lanzar segundo espejo"
                ),
            })
            estado[tid] = st
            ev = st.get("evidence", {})
            lineas.append(
                f"| {tid} | WAITING_EXECUTOR | activo={','.join(foreign_actives)} | "
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
            if ev.get("recovered_deviation"):
                current_dev = {
                    "type": "PATH_ESCAPE_RECOVERED",
                    "count": ev.get("executor_audit", {}).get("path_escape_count", 0),
                    "run_id": ev.get("executor_audit", {}).get("run_id"),
                }
                previous_dev = st.get("last_deviation", {})
                st["deviation_count"] = (
                    st.get("deviation_count", 0) + 1
                    if previous_dev.get("type") == current_dev["type"]
                    else 1
                )
                st["last_deviation"] = current_dev

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

    # Convergencia de una tarea dividida: los agentes no deciden el PASS padre.
    split_parent = str(focus_cfg.get("parent_task", "")).strip()
    if len(focus_tids) > 1 and split_parent in cfg.get("tareas", {}):
        child_states = {t: estado.get(t, {}).get("status") for t in focus_tids}
        if all(v == "PASS" for v in child_states.values()):
            rc, out = sh(
                ["bash", "-c", cfg["tareas"][split_parent]["acceptance"]],
                env={**os.environ, "SIMULADO": "1"},
            )
            pst = estado.get(split_parent, {"attempt": 0})
            pst["split_convergence"] = {
                "children": child_states,
                "acceptance_exit": rc,
                "tail": out[-1600:],
                "observed_sha": head,
            }
            if rc == 0:
                pst.update({
                    "status": "PASS",
                    "last_failure": "",
                    "next_action": "split A/B/C convergió; cierre global PASS",
                })
            else:
                pst.update({
                    "status": "REVISE",
                    "last_failure": "SPLIT_CONVERGENCE_FAIL",
                    "next_action": "revisar gate global T03 después de A/B/C",
                })
            estado[split_parent] = pst

    ESTADO.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    INFORME.parent.mkdir(parents=True, exist_ok=True)
    INFORME.write_text(
        "\n".join(lineas)
        + f"\n\nFoco: {focus_label}\nRelanzados: {', '.join(relanzar) or 'ninguno'}\n",
        encoding="utf-8",
    )
    print("\n".join(lineas))

    if relanzar:
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as g:
            g.write("relanzar=" + ",".join(relanzar) + "\n")


if __name__ == "__main__":
    main()
