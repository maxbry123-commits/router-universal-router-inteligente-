"""agentes/runtime/: los adaptadores buscan primero en <runtime>/bin (instalado por instalar-agentes.sh), sin romper RIU_*_BIN ni PATH.
instalado -> DISPONIBLE; ausente -> NO INSTALADO. Los scripts (instalar/verificar) se prueban con binarios falsos, sin red."""
import json
import os
import stat
import subprocess
import sys

import pytest

from agentes.adaptadores import _comun, disponibilidad, swe_agent

AGENTES_DIR = os.path.normpath(os.path.join(os.path.dirname(disponibilidad.__file__), ".."))
RUNTIME = os.path.join(AGENTES_DIR, "runtime")
VARS = ["RIU_CODEX_BIN", "RIU_CODEX_BASE_URL", "RIU_OPENCODE_BIN", "RIU_SWEAGENT_BIN", "RIU_DOCKER_BIN", "RIU_OPENHANDS_PYTHON", "RIU_CLAUDE_BIN",
        "RIU_CLAUDE_PASARELA_URL", "RIU_CLAUDE_PASARELA_MODELO", "OPENCLAW_GATEWAY_TOKEN", "RIU_SWEAGENT_IMAGE"]


@pytest.fixture
def rt(monkeypatch, tmp_path):
    """Runtime falso en tmp con PATH vacio y sin RIU_*_BIN."""
    for v in VARS:
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "sin-binarios"))
    monkeypatch.setenv("RIU_SWE_SONDA_MODELOS", "0")
    r = tmp_path / "runtime"
    (r / "bin").mkdir(parents=True)
    monkeypatch.setenv("RIU_AGENTES_RUNTIME", str(r))
    return r


def ejecutable(ruta, cuerpo="#!/bin/sh\necho v-falsa 1.2.3\n"):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(cuerpo)
    ruta.chmod(ruta.stat().st_mode | stat.S_IXUSR)
    return str(ruta)


def cap():
    return disponibilidad.capacidades(sonda_openhands=lambda py: True, sonda_gateway=lambda u: False, sonda_hf=lambda u: True)["agentes"]


# ---------------- ruta de busqueda ----------------
def test_el_runtime_por_defecto_es_agentes_runtime_dentro_del_repo(monkeypatch):
    monkeypatch.delenv("RIU_AGENTES_RUNTIME", raising=False)
    assert os.path.normpath(_comun.dir_runtime()) == RUNTIME


def test_binario_instalado_en_runtime_bin_se_encuentra(rt):
    exe = ejecutable(rt / "bin" / "codex")
    assert _comun.binario("codex", "RIU_CODEX_BIN") == exe


def test_binario_ausente_no_se_encuentra(rt):
    assert _comun.binario("codex", "RIU_CODEX_BIN") is None


def test_runtime_bin_va_antes_que_el_PATH(rt, monkeypatch, tmp_path):
    en_path = ejecutable(tmp_path / "otro" / "opencode")
    monkeypatch.setenv("PATH", os.path.dirname(en_path))
    exe = ejecutable(rt / "bin" / "opencode")
    assert _comun.binario("opencode", "RIU_OPENCODE_BIN") == exe


def test_PATH_sigue_funcionando_si_no_hay_runtime(rt, monkeypatch, tmp_path):
    en_path = ejecutable(tmp_path / "otro" / "opencode")
    monkeypatch.setenv("PATH", os.path.dirname(en_path))
    assert _comun.binario("opencode", "RIU_OPENCODE_BIN") == en_path


def test_RIU_BIN_manda_sobre_el_runtime_y_si_es_invalido_no_cae_al_runtime(rt, tmp_path):
    ejecutable(rt / "bin" / "codex")
    propio = ejecutable(tmp_path / "mio" / "codex")
    os.environ["RIU_CODEX_BIN"] = propio
    assert _comun.binario("codex", "RIU_CODEX_BIN") == propio
    os.environ["RIU_CODEX_BIN"] = str(tmp_path / "no-existe")
    assert _comun.binario("codex", "RIU_CODEX_BIN") is None  # comportamiento previo intacto: una variable mala no se "arregla" en silencio


def test_un_archivo_sin_permiso_de_ejecucion_en_runtime_no_cuenta(rt):
    p = rt / "bin" / "codex"
    p.write_text("x"); p.chmod(0o644)
    assert _comun.binario("codex", "RIU_CODEX_BIN") is None


# ---------------- disponibilidad: instalado -> DISPONIBLE; ausente -> NO INSTALADO ----------------
@pytest.mark.parametrize("agente,binario,extra", [("opencode", "opencode", {}), ("codex", "codex", {"RIU_CODEX_BASE_URL": "http://127.0.0.1:1/v1"}),
                                                  ("swe-agent", "sweagent", {})])
def test_agente_instalado_en_runtime_esta_DISPONIBLE_y_ausente_NO_INSTALADO(rt, monkeypatch, agente, binario, extra):
    for k, v in extra.items():
        monkeypatch.setenv(k, v)
    ausente = cap()[agente]
    assert ausente["estado"] == "NO INSTALADO" and ausente["disponible"] is False
    ejecutable(rt / "bin" / binario)
    if agente == "swe-agent":
        ejecutable(rt / "bin" / "docker")  # swe-agent ademas pide Docker; aqui basta uno falso de la misma ruta de busqueda
    visto = cap()[agente]
    assert visto["estado"] == "DISPONIBLE" and visto["disponible"] is True, visto


def test_claude_instalado_en_runtime_pasa_a_NO_CONFIGURADO_no_a_NO_INSTALADO(rt):
    assert cap()["claude-code"]["estado"] == "NO INSTALADO"
    ejecutable(rt / "bin" / "claude")
    assert cap()["claude-code"]["estado"] == "NO CONFIGURADO"


def test_openhands_usa_el_python_del_venv_del_runtime(rt, monkeypatch):
    assert _comun.python_openhands() == sys.executable  # sin venv: el Python del Harness, como antes
    py = ejecutable(rt / "venv" / "openhands" / "bin" / "python")
    assert _comun.python_openhands() == py
    assert cap()["openhands"]["estado"] == "DISPONIBLE"
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", sys.executable)  # la variable manda
    assert _comun.python_openhands() == sys.executable


def test_disponibilidad_no_lanza_nada_del_runtime(rt, tmp_path):
    marca = tmp_path / "lanzado"
    for b in ("codex", "opencode", "sweagent", "claude"):
        ejecutable(rt / "bin" / b, "#!/bin/sh\ntouch %s\n" % marca)
    cap()
    assert not marca.exists()


# ---------------- imagen por defecto de SWE-agent ----------------
def test_swe_agent_usa_por_defecto_la_imagen_riu_y_RIU_SWEAGENT_IMAGE_la_cambia(rt, monkeypatch, tmp_path):
    assert swe_agent.IMAGEN_POR_DEFECTO == "riu-sweagent:latest"
    log = tmp_path / "argv.json"
    ejecutable(rt / "bin" / "sweagent", "#!%s\nimport sys, json\njson.dump(sys.argv[1:], open(%r, 'w'))\nsys.exit(1)\n" % (sys.executable, str(log)))
    ejecutable(rt / "bin" / "docker")
    ws = tmp_path / "ws"; ws.mkdir()
    monkeypatch.setenv("RIU_AGENTES_LLM_BASE_URL", "http://127.0.0.1:1"); monkeypatch.setenv("RIU_AGENTES_LLM_API_KEY", "clave-ficticia-local")
    args = dict(tarea_id="t-1", modelo="hf/qwen2.5-coder-1.5b", objetivo="x", contexto="", checkpoint={}, permisos={"directorio": str(ws), "escritura": False, "ejecucion": False})
    swe_agent.run(**args)
    assert "--env.deployment.image=riu-sweagent:latest" in json.load(open(log))
    monkeypatch.setenv("RIU_SWEAGENT_IMAGE", "otra:1")
    swe_agent.run(**args)
    assert "--env.deployment.image=otra:1" in json.load(open(log))


# ---------------- versionado: solo scripts y lockfiles ----------------
def test_el_runtime_versionado_tiene_scripts_y_lockfiles_y_ignora_binarios():
    for f in ("instalar-agentes.sh", "verificar-agentes.sh", ".gitignore", "node-agentes/package.json", "node-agentes/package-lock.json",
              "node-claude/package.json", "node-claude/package-lock.json", "node-openclaw/package.json", "node-openclaw/package-lock.json",
              "requirements-openhands.txt", "requirements-sweagent.txt"):
        assert os.path.isfile(os.path.join(RUNTIME, f)), f
    # el .gitignore se prueba en un repo temporal (en una maquina con runtime instalado, venv/ o node/ pueden ser enlaces y git no mira "mas alla" de un enlace)
    import shutil, tempfile
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(["git", "init", "-q", t], check=True)
        os.makedirs(os.path.join(t, "runtime"))
        shutil.copy(os.path.join(RUNTIME, ".gitignore"), os.path.join(t, "runtime", ".gitignore"))
        ignorados = ["runtime/bin/codex", "runtime/bin", "runtime/venv/openhands/bin/python", "runtime/venv", "runtime/node/agentes/node_modules/x", "runtime/node",
                     "runtime/node-agentes/node_modules/x", "runtime/node24/bin/node", "runtime/.node24.tmp/extraccion", "runtime/estado-agentes.json", "runtime/.instalado/codex", "runtime/.instalar.lock"]
        versionados = ["runtime/instalar-agentes.sh", "runtime/verificar-agentes.sh", "runtime/entorno.sh", "runtime/requirements-sweagent.txt", "runtime/node-agentes/package-lock.json"]
        r = subprocess.run(["git", "-C", t, "check-ignore"] + ignorados + versionados, capture_output=True, text=True)
        assert sorted(r.stdout.split()) == sorted(ignorados), r.stdout


@pytest.mark.parametrize("script", ["instalar-agentes.sh", "verificar-agentes.sh"])
def test_scripts_sintaxis_bash_y_ejecutables(script):
    p = os.path.join(RUNTIME, script)
    assert os.access(p, os.X_OK)
    assert subprocess.run(["bash", "-n", p]).returncode == 0
    texto = open(p, encoding="utf-8").read()
    assert "set -euo pipefail" in texto


def test_lockfiles_fijan_las_versiones_pedidas():
    leer = lambda f: open(os.path.join(RUNTIME, f), encoding="utf-8").read()
    ag = json.loads(leer("node-agentes/package.json"))["dependencies"]
    assert ag == {"@openai/codex": "0.166.0", "opencode-ai": "1.19.5"}  # exactas, sin ^
    assert json.loads(leer("node-claude/package.json"))["dependencies"] == {"@anthropic-ai/claude-code": "2.1.316"}
    assert json.loads(leer("node-openclaw/package.json"))["dependencies"] == {"openclaw": "2026.6.35"}
    assert "openhands-sdk==1.59.0" in leer("requirements-openhands.txt") and "openhands-tools==1.59.0" in leer("requirements-openhands.txt")
    assert "swe-rex" in leer("requirements-sweagent.txt")


# ---------------- verificar-agentes.sh con binarios falsos ----------------
def correr_verificar(rt, tmp_path, extra_env=None):
    salida = tmp_path / "estado.json"
    env = {**os.environ, "RIU_AGENTES_RUNTIME": str(rt), "PATH": "/usr/bin:/bin", "RIU_ESTADO_JSON": str(salida), **(extra_env or {})}
    r = subprocess.run(["bash", os.path.join(RUNTIME, "verificar-agentes.sh")], capture_output=True, text=True, env=env, timeout=120)
    return r, salida


def test_verificar_escribe_json_con_versiones_reales_ejecutadas_y_sin_secretos(rt, tmp_path):
    ejecutable(rt / "bin" / "codex", "#!/bin/sh\necho 'codex-cli 9.9.9'\n")
    ejecutable(rt / "bin" / "opencode", "#!/bin/sh\necho 1.2.3\n")
    ejecutable(rt / "bin" / "claude", "#!/bin/sh\necho '3.0.0 (Claude Code)'\n")
    ejecutable(rt / "bin" / "sweagent", "#!/bin/sh\necho 'usage: sweagent'\n")
    ejecutable(rt / "bin" / "openclaw", "#!/bin/sh\necho 'OpenClaw 2026.1.1 (abc)'\n")
    r, salida = correr_verificar(rt, tmp_path, {"GROQ_API_KEY": "gsk_clave-falsa-de-prueba-1234567890", "GITHUB_TOKEN": "ghp_falso1234567890abcdefgh"})
    datos = json.loads(salida.read_text())
    ag = datos["agentes"]
    assert ag["codex"]["instalado"] is True and ag["codex"]["version"] == "codex-cli 9.9.9"
    assert ag["opencode"]["version"] == "1.2.3" and ag["claude-code"]["version"].startswith("3.0.0")
    assert ag["swe-agent"]["instalado"] is True and ag["openclaw"]["instalado"] is True
    assert ag["openhands"]["instalado"] is False  # sin venv de openhands en este runtime
    assert "gsk_" not in salida.read_text() and "ghp_" not in salida.read_text() and "gsk_" not in r.stdout + r.stderr
    assert datos["runtime"] and "generado" in datos


def test_verificar_marca_ausente_lo_que_no_esta(rt, tmp_path):
    r, salida = correr_verificar(rt, tmp_path)
    datos = json.loads(salida.read_text())
    assert all(v["instalado"] is False and v["version"] is None for v in datos["agentes"].values())
    assert set(datos["agentes"]) == {"codex", "opencode", "swe-agent", "openhands", "claude-code", "openclaw"}


def test_verificar_un_binario_que_falla_no_cuenta_como_instalado_con_version(rt, tmp_path):
    ejecutable(rt / "bin" / "codex", "#!/bin/sh\necho roto >&2\nexit 3\n")
    r, salida = correr_verificar(rt, tmp_path)
    c = json.loads(salida.read_text())["agentes"]["codex"]
    assert c["instalado"] is True and c["version"] is None and c["ok"] is False


# ---------------- entorno.sh: exporta PATH / RIU_*_BIN sin pisar lo existente ----------------
def test_entorno_exporta_path_y_RIU_BIN_del_runtime_sin_pisar_los_ya_definidos(rt, tmp_path):
    codex = ejecutable(rt / "bin" / "codex"); ejecutable(rt / "bin" / "opencode")
    py = ejecutable(rt / "venv" / "openhands" / "bin" / "python")
    propio = ejecutable(tmp_path / "mio" / "opencode")
    env = {"PATH": "/usr/bin:/bin", "RIU_AGENTES_RUNTIME": str(rt), "RIU_OPENCODE_BIN": propio, "HOME": str(tmp_path)}
    r = subprocess.run(["bash", "-c", 'source "%s"; echo "$PATH"; echo "$RIU_CODEX_BIN"; echo "$RIU_OPENCODE_BIN"; echo "$RIU_OPENHANDS_PYTHON"; echo "[${RIU_SWEAGENT_BIN:-}]"'
                        % os.path.join(RUNTIME, "entorno.sh")], capture_output=True, text=True, env=env)
    path, c, o, p, s = r.stdout.splitlines()
    assert path.startswith(str(rt / "bin") + ":") and c == codex and o == propio and p == py and s == "[]"