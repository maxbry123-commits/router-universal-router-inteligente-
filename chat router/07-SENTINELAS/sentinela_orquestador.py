"""SENTINELA ORQUESTADOR — bucle de recuperación de tareas (contrato: chat router/07-SENTINELAS/CONTRATOS.yaml).

Cerebro determinista (decide PASS): archivos requeridos en main con contenido, sin rutas fugadas, pytest exit code, informe, commit.
Cerebro investigador (solo si REVISE): research packet (error literal) → GitHub issues del componente → modelo NVIDIA redacta causa + orden.
Nunca un LLM decide PASS. Estado por tarea persistente en ESTADO-TAREAS.json (continúa el intento anterior; no empieza de cero).
Uso: python sentinela_orquestador.py   (en la raíz del repo, con GH_TOKEN y NVIDIA_API_KEY_1..4 en el entorno)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import urllib.request

import yaml

BASE = pathlib.Path("chat router/07-SENTINELAS")
CONTRATOS = BASE / "CONTRATOS.yaml"
ESTADO = BASE / "ESTADO-TAREAS.json"
INFORME = BASE / "informes/ORQUESTADOR.md"
TAREAS_DIR = pathlib.Path("chat router/06-ESPEJOS/tareas")
REPO = "maxbry123-commits/router-universal-router-inteligente-"
WF = "claude-code-espejos.yml"
MAX_INTENTOS = 3


def sh(cmd: list[str], timeout: int = 300, env: dict | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, (p.stdout + p.stderr)[-4000:]
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def ahora() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def espejos_activos() -> set[str]:
    rc, out = sh(["gh", "run", "list", "-R", REPO, "-w", WF, "-s", "in_progress", "--json", "databaseId", "-L", "10"])
    activos: set[str] = set()
    if rc != 0:
        return activos
    for r in json.loads(out or "[]"):
        rc2, jobs = sh(["gh", "run", "view", str(r["databaseId"]), "-R", REPO, "--json", "jobs"])
        for j in json.loads(jobs or "{}").get("jobs", []):
            if j.get("status") != "completed" and "(" in j.get("name", ""):
                activos.add(j["name"].split("(")[-1].rstrip(")"))
    return activos


def verificar(tid: str, c: dict, prohibido: list[str]) -> dict:
    scope = pathlib.Path(c["scope"])
    faltan = [f for f in c["required_files"] if not (scope / f).is_file() or (scope / f).stat().st_size == 0]
    fugas = [p for p in prohibido if pathlib.Path(p).exists() and "chat router/chat router" in p]
    rc, out = sh(["bash", "-c", c["acceptance"]], env={**os.environ, "SIMULADO": "1"})
    informe = pathlib.Path(f"chat router/06-ESPEJOS/informes/{tid}.md")
    rcg, log = sh(["git", "log", "-1", "--format=%H %s", "--", c["scope"]])
    ev = {"faltan": faltan, "fugas": fugas, "pytest_exit": rc, "pytest_tail": out[-1200:],
          "informe": informe.is_file() and informe.stat().st_size > 0, "ultimo_commit": log.strip()[:120]}
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


def nvidia(prompt: str) -> str:
    for kn in ("NVIDIA_API_KEY_1", "NVIDIA_API_KEY_2", "NVIDIA_API_KEY_3", "NVIDIA_API_KEY_4"):
        key = os.environ.get(kn)
        if not key:
            continue
        for model in ("moonshotai/kimi-k3", "z-ai/glm-5.3", "z-ai/glm-5.3-flash"):
            body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 900, "temperature": 0.1}).encode()
            req = urllib.request.Request("https://integrate.api.nvidia.com/v1/chat/completions", data=body,
                                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return json.loads(r.read())["choices"][0]["message"]["content"]
            except Exception:  # noqa: BLE001
                continue
    return ""


def investigar(tid: str, c: dict, ev: dict, intento: int) -> dict:
    error = ev.get("pytest_tail", "")[-600:] or ev.get("causa", "")
    clave = next((l for l in error.splitlines()[::-1] if "Error" in l or "error" in l or "FAILED" in l), ev.get("causa", ""))[:120]
    fuentes = []
    for repo in ("Aider-AI/aider", "pytest-dev/pytest"):
        rc, out = sh(["gh", "search", "issues", clave, "--repo", repo, "--limit", "3", "--json", "title,url"])
        if rc == 0:
            fuentes += json.loads(out or "[]")
    prompt = (f"Eres el INVESTIGADOR del sentinela. Tarea {tid}: {c['objective']}. Alcance: {c['scope']}. Intento {intento}.\n"
              f"Veredicto determinista: {ev['veredicto']} causa={ev.get('causa')} faltan={ev['faltan']} pytest_exit={ev['pytest_exit']}\n"
              f"Error literal:\n{error}\nFuentes encontradas: {json.dumps(fuentes)[:1500]}\n"
              "Responde en español, máximo 12 líneas, formato exacto:\nCAUSA_RAIZ: ...\nNO_REGENERAR: (archivos que ya están bien)\n"
              "ARREGLAR: (pasos concretos)\nACEPTACION: " + c["acceptance"])
    return {"clave_busqueda": clave, "fuentes": fuentes[:6], "analisis": nvidia(prompt) or "sin respuesta del modelo"}


def ordenar(tid: str, intento: int, ev: dict, rp: dict) -> None:
    f = TAREAS_DIR / f"{tid}.md"
    if not f.is_file():
        return
    f.write_text(f.read_text(encoding="utf-8") + f"\n\n## CORRECCIÓN DEL SENTINELA (intento {intento}, {ahora()})\n"
                 f"Veredicto: {ev['veredicto']} · causa: {ev.get('causa')} · faltan: {ev['faltan']} · pytest exit: {ev['pytest_exit']}\n"
                 f"{rp['analisis']}\nNo declares éxito: solo cuenta PASS cuando todos los archivos existen y el comando de aceptación sale con código 0.\n",
                 encoding="utf-8")


def main() -> None:
    cfg = yaml.safe_load(CONTRATOS.read_text(encoding="utf-8"))
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    head = sh(["git", "rev-parse", "HEAD"])[1].strip()
    activos = espejos_activos()
    relanzar, lineas = [], [f"# SENTINELA ORQUESTADOR — {ahora()} · observed_sha {head[:10]}", "", "| Tarea | Estado | Causa | Intento | Evidencia |", "|---|---|---|---|---|"]
    for tid, c in cfg["tareas"].items():
        st = estado.get(tid, {"attempt": 0})
        if tid in activos:
            st.update({"status": "ACTIVE", "last_sha": head})
        else:
            ev = verificar(tid, c, cfg.get("prohibido_global", []))
            st.update({"last_sha": head, "evidence": ev})
            if ev["veredicto"] == "PASS":
                st.update({"status": "PASS", "next_action": "ninguna"})
            elif st.get("attempt", 0) >= MAX_INTENTOS:
                st.update({"status": "BLOCKED", "next_action": "revisión de Opus/Director", "last_failure": ev.get("causa")})
            else:
                st["attempt"] = st.get("attempt", 0) + 1
                rp = investigar(tid, c, ev, st["attempt"])
                ordenar(tid, st["attempt"], ev, rp)
                st.update({"status": "REVISE", "last_failure": ev.get("causa"), "research_packet": rp, "next_action": "espejo relanzado"})
                relanzar.append(tid)
        estado[tid] = st
        ev = st.get("evidence", {})
        lineas.append(f"| {tid} | {st['status']} | {st.get('last_failure', '')} | {st.get('attempt', 0)} | faltan {len(ev.get('faltan', []))} · pytest {ev.get('pytest_exit', '-')} |")
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    INFORME.parent.mkdir(parents=True, exist_ok=True)
    INFORME.write_text("\n".join(lineas) + f"\n\nRelanzados: {', '.join(relanzar) or 'ninguno'}\n", encoding="utf-8")
    print("\n".join(lineas))
    if relanzar:
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as g:
            g.write("relanzar=" + ",".join(relanzar) + "\n")


if __name__ == "__main__":
    main()
