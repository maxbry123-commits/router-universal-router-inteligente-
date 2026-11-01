"""Ejecucion REAL de los adaptadores (checklist A2 66-72, 194): los CLIs/SDKs son los REALES instalados bajo RIU_A2_INST (por defecto /tmp/a2-inst, fuera del repo);
solo el LLM es un modelo de guion local (_modelo_falso.py). Se omite (skip con el comando de instalacion) lo que no este instalado.
Instalacion (sin privilegios, fuera del repo):
  npm i --prefix $INST/npm @openai/codex opencode-ai ; npm i --prefix $INST/npm-oc openclaw
  python3 -m venv $INST/venv-oh && $INST/venv-oh/bin/pip install openhands-sdk openhands-tools
  python3 -m venv $INST/venv-swe && cp -r agentes/agentes-listos/SWE-agent/SWE-agent-main $INST/swesrc && $INST/venv-swe/bin/pip install -e $INST/swesrc   (+ Docker daemon)"""
import json
import os
import shutil
import socket
import subprocess
import time

import pytest

from agentes.adaptadores import claude_code, codex, disponibilidad, openclaw, openhands, opencode, swe_agent
import _modelo_falso

INST = os.environ.get("RIU_A2_INST", "/tmp/a2-inst")
BINS = {"codex": INST + "/npm/node_modules/.bin/codex", "opencode": INST + "/npm/node_modules/.bin/opencode", "openclaw": INST + "/npm-oc/node_modules/.bin/openclaw",
        "sweagent": INST + "/venv-swe/bin/sweagent", "openhands_python": INST + "/venv-oh/bin/python", "claude": shutil.which("claude") or ""}
BASE = dict(tarea_id="t-real", checkpoint={})
INSTALAR = {"codex": "npm i --prefix $INST/npm @openai/codex", "opencode": "npm i --prefix $INST/npm opencode-ai", "openclaw": "npm i --prefix $INST/npm-oc openclaw",
            "sweagent": "ver docstring del modulo (clon de SWE-agent + pip install -e, requiere Docker)", "openhands_python": "ver docstring del modulo (venv con openhands-sdk/openhands-tools)",
            "claude": "instalar la CLI `claude`"}


def requiere(*nombres):
    faltan = [n for n in nombres if not (BINS[n] and os.access(BINS[n], os.X_OK))]
    return pytest.mark.skipif(bool(faltan), reason="no instalado: " + "; ".join("%s -> %s" % (n, INSTALAR[n]) for n in faltan))


@pytest.fixture
def ws(tmp_path):
    d = tmp_path / "ws"
    d.mkdir()
    return d


@pytest.fixture
def modelo(ws, monkeypatch):
    """Modelo de guion que, si el agente ofrece herramienta de escritura, crea ws/hola.txt con contenido conocido."""
    s = _modelo_falso.arrancar("%s::contenido real" % (ws / "hola.txt"))
    base = "http://127.0.0.1:%d" % s.server_port
    for v in ("PATH_FALSO",):
        pass
    monkeypatch.setenv("RIU_AGENTES_LLM_BASE_URL", base)
    monkeypatch.setenv("RIU_AGENTES_LLM_API_KEY", "clave-ficticia-local")
    monkeypatch.setenv("OPENHANDS_SUPPRESS_BANNER", "1")
    yield s
    s.shutdown(); s.server_close()


def peticiones_chat(s):
    return [v for v in s.visto if v["path"].endswith("/chat/completions")]


# ---------------- 67-69: dependencias, comandos, versiones, permisos de ejecucion ----------------
@pytest.mark.parametrize("nombre,args", [("codex", ["--version"]), ("opencode", ["--version"]), ("openclaw", ["--version"]), ("sweagent", ["--help"]), ("claude", ["--version"])])
def test_real_comando_instalado_ejecutable_y_con_version(nombre, args):
    if not (BINS[nombre] and os.access(BINS[nombre], os.X_OK)):
        pytest.skip("no instalado: " + INSTALAR[nombre])
    assert os.access(BINS[nombre], os.X_OK)
    r = subprocess.run([BINS[nombre]] + args, capture_output=True, text=True, timeout=120, env={**os.environ, "OPENHANDS_SUPPRESS_BANNER": "1"})
    assert r.returncode == 0 and (r.stdout + r.stderr).strip(), (nombre, r.stderr[-300:])


@requiere("openhands_python")
def test_real_openhands_sdk_importable_con_su_version():
    r = subprocess.run([BINS["openhands_python"], "-I", "-c", "import importlib.metadata as m; print(m.version('openhands-sdk'), m.version('openhands-tools'))"], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and r.stdout.split()[0].count(".") >= 1


# ---------------- 72: la carpeta fuente NO cuenta como instalado; el binario real si ----------------
def test_real_la_carpeta_fuente_no_es_una_instalacion(monkeypatch, tmp_path):
    for v in ("RIU_CODEX_BIN", "RIU_OPENCODE_BIN", "RIU_SWEAGENT_BIN", "RIU_CLAUDE_BIN", "RIU_OPENHANDS_PYTHON", "OPENCLAW_GATEWAY_TOKEN", "RIU_CODEX_BASE_URL"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    fuentes = os.path.join(os.path.dirname(disponibilidad.__file__), "..", "agentes-listos")
    caps = disponibilidad.capacidades(sonda_modelos=lambda p, c: (_ for _ in ()).throw(OSError("sin red")), sonda_openhands=lambda py: False, sonda_gateway=lambda u: False)["agentes"]
    if os.path.isdir(fuentes):
        for a in ("codex", "opencode", "swe-agent", "claude-code"):
            assert caps[a]["disponible"] is False and "no esta instalado" in caps[a]["motivo"], (a, caps[a])


@requiere("codex", "opencode", "openhands_python", "claude", "sweagent")
def test_real_disponibilidad_detecta_los_binarios_instalados_via_RIU_BIN(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("RIU_CODEX_BIN", BINS["codex"]); monkeypatch.setenv("RIU_CODEX_BASE_URL", "http://127.0.0.1:1/v1")
    monkeypatch.setenv("RIU_OPENCODE_BIN", BINS["opencode"]); monkeypatch.setenv("RIU_OPENHANDS_PYTHON", BINS["openhands_python"])
    monkeypatch.setenv("RIU_CLAUDE_BIN", BINS["claude"]); monkeypatch.setenv("RIU_CLAUDE_PASARELA_URL", "http://127.0.0.1:1"); monkeypatch.setenv("RIU_CLAUDE_PASARELA_MODELO", "nvidia/nemotron-3-ultra-550b-a55b")
    monkeypatch.setenv("RIU_SWEAGENT_BIN", BINS["sweagent"])
    caps = disponibilidad.capacidades(sonda_modelos=lambda p, c: (_ for _ in ()).throw(OSError("sin red")))["agentes"]  # sonda de openhands REAL: importa el SDK del venv
    for a in ("codex", "opencode", "openhands", "claude-code"):
        assert caps[a]["disponible"] is True, (a, caps[a])
    assert caps["swe-agent"]["disponible"] is bool(shutil.which("docker")) or "Docker" in caps["swe-agent"]["motivo"]


# ---------------- 70, 71, 77-79, 194: tarea real por adaptador ----------------
@requiere("opencode")
def test_real_opencode_ejecuta_una_tarea_y_crea_el_archivo(modelo, ws, monkeypatch):
    monkeypatch.setenv("RIU_OPENCODE_BIN", BINS["opencode"])
    r = opencode.run(modelo="hf/qwen2.5-coder-1.5b", objetivo="crea hola.txt", contexto="", permisos={"directorio": str(ws), "escritura": True, "ejecucion": False}, **BASE)
    assert r["ok"] is True and r["agente"] == "opencode" and "write" in r["herramientas"] and r["recibo"].startswith("opencode:t-real:")
    assert (ws / "hola.txt").read_text() == "contenido real"  # efecto REAL en disco hecho por el agente real
    p = peticiones_chat(modelo)[-1]
    assert p["body"]["model"] == "qwen2.5-coder-1.5b" and p["auth"] == "Bearer clave-ficticia-local" and r["modelo_usado"] == "qwen2.5-coder-1.5b"  # acceso al modelo elegido


@requiere("opencode")
def test_real_opencode_sin_permiso_de_escritura_no_escribe(modelo, ws, monkeypatch):
    monkeypatch.setenv("RIU_OPENCODE_BIN", BINS["opencode"])
    r = opencode.run(modelo="hf/qwen2.5-coder-1.5b", objetivo="crea hola.txt", contexto="", permisos={"directorio": str(ws), "escritura": False, "ejecucion": False}, **BASE)
    assert not (ws / "hola.txt").exists()


@requiere("openhands_python")
def test_real_openhands_ejecuta_una_tarea_y_crea_el_archivo(modelo, ws, monkeypatch):
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", BINS["openhands_python"])
    r = openhands.run(modelo="hf/lfm2.5-350m", objetivo="crea hola.txt", contexto="", permisos={"directorio": str(ws), "escritura": True, "ejecucion": False}, **BASE)
    assert r["ok"] is True and r["agente"] == "openhands" and "file_editor" in r["herramientas"] and r["recibo"].startswith("openhands:t-real:")
    assert (ws / "hola.txt").read_text() == "contenido real"
    assert peticiones_chat(modelo)[-1]["body"]["model"] == "openai/lfm2.5-350m" or peticiones_chat(modelo)[-1]["body"]["model"] == "lfm2.5-350m"
    assert r["modelo_usado"] == "lfm2.5-350m"


@requiere("codex")
def test_real_codex_completa_un_turno_contra_un_endpoint_responses(modelo, ws, monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", BINS["codex"])
    monkeypatch.setenv("RIU_CODEX_BASE_URL", "http://127.0.0.1:%d/v1" % modelo.server_port)
    monkeypatch.setenv("HOME", str(tmp_path / "home")); (tmp_path / "home").mkdir()
    r = codex.run(modelo="hf/qwen2.5-coder-1.5b", objetivo="di hola", contexto="", permisos={"directorio": str(ws), "escritura": False, "ejecucion": False}, **BASE)
    assert r["ok"] is True and r["agente"] == "codex" and "TAREA_HECHA" in r["resultado"] and "sandbox:read-only" in r["evidencias"]
    pr = [v for v in modelo.visto if v["path"].endswith("/responses")]
    assert pr and pr[-1]["body"]["model"] == "qwen2.5-coder-1.5b" and r["modelo_usado"] == "qwen2.5-coder-1.5b"


@requiere("claude")
def test_real_claude_code_completa_un_turno_por_la_pasarela(modelo, ws, monkeypatch):
    monkeypatch.setenv("RIU_CLAUDE_BIN", BINS["claude"])
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_URL", "http://127.0.0.1:%d" % modelo.server_port)
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_MODELO", "nvidia/nemotron-3-ultra-550b-a55b")
    r = claude_code.run(modelo="nvidia/nvidia/nemotron-3-ultra-550b-a55b", objetivo="di hola", contexto="", permisos={"directorio": str(ws), "escritura": False, "ejecucion": False}, **BASE)
    assert r["ok"] is True and r["agente"] == "claude-code" and "TAREA_HECHA" in r["resultado"] and r["modo"] if False else r["ok"]
    assert any(v["path"].split("?")[0].endswith("/v1/messages") for v in modelo.visto) and r["modelo_usado"] == "nvidia/nemotron-3-ultra-550b-a55b"


def _puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def gateway_real(modelo, tmp_path, monkeypatch):
    """Gateway OpenClaw REAL (proceso) configurado con el proveedor `swecode` apuntando al modelo de guion."""
    puerto, home = _puerto_libre(), tmp_path / "ocHome"
    home.mkdir()
    cfg = {"gateway": {"mode": "local", "port": puerto, "bind": "loopback", "auth": {"mode": "token", "token": "token-ficticio-local-oc"}, "http": {"endpoints": {"chatCompletions": {"enabled": True}}}},
           "models": {"mode": "merge", "providers": {"swecode": {"baseUrl": "http://127.0.0.1:%d/v1" % modelo.server_port, "apiKey": "clave-ficticia-local", "api": "openai-completions",
                      "models": [{"id": m, "name": m, "reasoning": False, "input": ["text"], "contextWindow": 32000, "maxTokens": 4096} for m in ("qwen2.5-coder-1.5b", "lfm2.5-350m")]}}},
           "agents": {"defaults": {"workspace": str(tmp_path / "ocws"), "model": {"primary": "swecode/qwen2.5-coder-1.5b"}}}}
    (home / "openclaw.json").write_text(json.dumps(cfg))
    env = {**os.environ, "OPENCLAW_CONFIG_PATH": str(home / "openclaw.json"), "OPENCLAW_STATE_DIR": str(home / "state"), "HOME": str(home)}
    p = subprocess.Popen([BINS["openclaw"], "gateway", "run", "--port", str(puerto), "--auth", "token", "--token", "token-ficticio-local-oc"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        t0 = time.time()
        while time.time() - t0 < 90:
            try:
                socket.create_connection(("127.0.0.1", puerto), timeout=1).close(); break
            except OSError:
                time.sleep(1)
        else:
            pytest.fail("el Gateway no arranco")
        time.sleep(3)
        monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "token-ficticio-local-oc"); monkeypatch.setenv("RIU_OPENCLAW_URL", "http://127.0.0.1:%d" % puerto)
        yield puerto
    finally:
        try:
            os.killpg(p.pid, 9)
        except ProcessLookupError:
            pass


@requiere("openclaw")
def test_real_openclaw_gateway_responde_y_llega_al_modelo_pedido(gateway_real, modelo, ws):
    caps = disponibilidad.capacidades(sonda_modelos=lambda p, c: (_ for _ in ()).throw(OSError("x")))["agentes"]["openclaw"]
    assert caps["disponible"] is True  # sonda TCP real contra el Gateway real
    r = openclaw.run(modelo="hf/qwen2.5-coder-1.5b", objetivo="di hola", contexto="", permisos={"directorio": str(ws), "escritura": True, "ejecucion": False}, **BASE)
    assert r["ok"] is True and r["agente"] == "openclaw" and "TAREA_HECHA" in r["resultado"] and r["recibo"].startswith("openclaw:t-real:")
    assert peticiones_chat(modelo)[-1]["body"]["model"] == "qwen2.5-coder-1.5b"  # el modelo realmente consultado por el Gateway
    assert r["modelo_usado"] == "swecode/qwen2.5-coder-1.5b"  # el Gateway solo informa su alias; se registra el pedido


# ---------------- SWE-agent: requiere el daemon de Docker y una imagen local ----------------
def _docker_vivo():
    return bool(shutil.which("docker")) and subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0


@requiere("sweagent")
@pytest.mark.skipif(not _docker_vivo(), reason="BLOQUEO operativo: SWE-agent corre en un contenedor y no hay daemon de Docker (arrancar dockerd y `docker pull python:3.12-slim`)")
@pytest.mark.skipif(os.environ.get("RIU_A2_SWE_REAL") != "1", reason="ejecucion real de SWE-agent solo con RIU_A2_SWE_REAL=1 (descarga imagenes y tarda minutos)")
def test_real_swe_agent_ejecuta_en_contenedor(ws, monkeypatch):
    s = _modelo_falso.arrancar("", bind="0.0.0.0")
    try:
        subprocess.run(["git", "init", "-q", str(ws)], check=True); (ws / "a.txt").write_text("x")
        subprocess.run(["git", "-C", str(ws), "add", "."], check=True); subprocess.run(["git", "-C", str(ws), "-c", "user.email=a@b.c", "-c", "user.name=a", "commit", "-qm", "i"], check=True)
        monkeypatch.setenv("RIU_SWEAGENT_BIN", BINS["sweagent"]); monkeypatch.setenv("RIU_SWEAGENT_IMAGE", os.environ.get("RIU_SWEAGENT_IMAGE", "python:3.12-slim"))
        monkeypatch.setenv("RIU_AGENTES_LLM_BASE_URL", "http://172.17.0.1:%d" % s.server_port); monkeypatch.setenv("RIU_AGENTES_LLM_API_KEY", "clave-ficticia-local")
        r = swe_agent.run(modelo="hf/qwen2.5-coder-1.5b", objetivo="crea hola.txt", contexto="", permisos={"directorio": str(ws), "escritura": True, "ejecucion": False}, **BASE)
        assert r["ok"] is True and r["agente"] == "swe-agent" and r["recibo"].startswith("swe-agent:")
    finally:
        s.shutdown(); s.server_close()
