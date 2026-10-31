"""Los 6 adaptadores contra su interfaz REAL, con ejecutables/servidor FALSOS locales (no hay software real instalado aqui).
Cubre camino feliz, argumentos exactos (lista, sin shell), permisos, claves fuera de argv/resultado, y rutas de error:
AGENTE_NO_INSTALADO (nunca ok:true), salida != 0, timeout, entradas invalidas."""
import json
import os
import re
import stat
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from agentes.adaptadores import claude_code, codex, openclaw, openhands, opencode, swe_agent

CLAVE_FICTICIA = "clave-ficticia-solo-prueba-0001"
BASE = dict(tarea_id="t-1", modelo="hf/qwen2.5-coder-1.5b", objetivo="corrige el bug", contexto="ctx previo", checkpoint={"paso": 0})


def fake(tmp_path, nombre, cuerpo):
    """Ejecutable falso: registra argv, stdin, cwd y entorno en <nombre>.log y ejecuta `cuerpo` (Python)."""
    p = tmp_path / nombre
    p.write_text("#!%s\nimport sys, os, json\n_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), %r + '.log')\n"
                 "_in = sys.stdin.read() if not sys.stdin.isatty() else ''\n"
                 "open(_log, 'a').write(json.dumps({'argv': sys.argv[1:], 'stdin': _in, 'cwd': os.getcwd(), 'env': dict(os.environ)}) + '\\n')\n%s\n"
                 % (sys.executable, nombre, cuerpo))
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def llamadas(tmp_path, nombre):
    return [json.loads(l) for l in (tmp_path / (nombre + ".log")).read_text().splitlines()]


@pytest.fixture(autouse=True)
def entorno(monkeypatch, tmp_path):
    for v in ("RIU_CODEX_BIN", "RIU_OPENCODE_BIN", "RIU_SWEAGENT_BIN", "RIU_OPENHANDS_PYTHON", "RIU_CLAUDE_BIN", "RIU_DOCKER_BIN",
              "OPENCLAW_GATEWAY_TOKEN", "RIU_OPENCLAW_URL", "RIU_CLAUDE_PASARELA_URL", "RIU_CLAUDE_PASARELA_MODELO", "RIU_CODEX_BASE_URL",
              "GROQ_API_KEY", "NVIDIA_API_KEY", "RIU_AGENTES_LLM_API_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("RIU_SWE_BRIDGE_URL", "http://127.0.0.1:7870")
    monkeypatch.setenv("PATH", str(tmp_path / "vacio"))  # sin binarios reales en PATH
    (tmp_path / "vacio").mkdir()
    monkeypatch.setenv("RIU_API_KEY", "secreto-del-harness-no-debe-pasar")


def permisos(tmp_path, **kw):
    d = tmp_path / "ws"
    d.mkdir(exist_ok=True)
    return {"directorio": str(d), **kw}


def comunes_ok(r, agente):
    assert r["ok"] is True and r["agente"] == agente and r["task_id"] == "t-1" and r["exit_code"] == 0
    assert r["recibo"].startswith(agente + ":t-1:") and isinstance(r["herramientas"], list) and isinstance(r["evidencias"], list)
    assert "RIU_API_KEY" not in json.dumps(r) and "secreto-del-harness" not in json.dumps(r)


# ---------------- codex ----------------
CODEX_OK = ("o = sys.argv[sys.argv.index('-o') + 1]\nopen(o, 'w').write('listo: bug corregido')\n"
            "print(json.dumps({'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'pytest'}}))\n"
            "print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'listo'}}))")


def test_codex_camino_feliz_solo_lectura_por_defecto(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", fake(tmp_path, "codex", CODEX_OK))
    r = codex.run(permisos=permisos(tmp_path), **BASE)
    comunes_ok(r, "codex")
    assert r["resultado"] == "listo: bug corregido" and "command_execution" in r["herramientas"]
    c = llamadas(tmp_path, "codex")[0]
    a = c["argv"]
    assert a[0] == "exec" and "--json" in a and a[a.index("-m") + 1] == "qwen2.5-coder-1.5b" and a[a.index("-s") + 1] == "read-only"
    assert a[a.index("-C") + 1] == os.path.realpath(str(tmp_path / "ws")) and "danger-full-access" not in a and not any("dangerously" in x or x == "--yolo" for x in a)
    assert any("model_providers.riu" in x and "http://127.0.0.1:7870/v1" in x and 'wire_api="responses"' in x for x in a)
    assert "corrige el bug" in c["stdin"] and "ctx previo" in c["stdin"] and "corrige el bug" not in " ".join(a)
    assert "RIU_API_KEY" not in c["env"] and c["env"]["RIU_AGENTE_LLM_KEY"] == "no-requerida"


def test_codex_escritura_usa_workspace_write(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", fake(tmp_path, "codex", CODEX_OK))
    codex.run(permisos=permisos(tmp_path, escritura=True), **BASE)
    a = llamadas(tmp_path, "codex")[0]["argv"]
    assert a[a.index("-s") + 1] == "workspace-write"


def test_codex_clave_de_groq_solo_en_entorno_del_hijo(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", fake(tmp_path, "codex", CODEX_OK))
    monkeypatch.setenv("GROQ_API_KEY", CLAVE_FICTICIA)
    r = codex.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "groq/qwen/qwen3.8-27b"})
    c = llamadas(tmp_path, "codex")[0]
    assert CLAVE_FICTICIA not in " ".join(c["argv"]) and CLAVE_FICTICIA not in json.dumps(r) and c["env"]["RIU_AGENTE_LLM_KEY"] == CLAVE_FICTICIA
    assert any("https://api.groq.com/openai/v1" in x for x in c["argv"])


def test_codex_no_instalado_no_finge(tmp_path):
    r = codex.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_INSTALADO" and r["efectos_posibles"] is False and r["recibo"] is None
    assert "RIU_CODEX_BIN" in r["error"]


def test_codex_salida_con_error_pudo_tener_efectos(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", fake(tmp_path, "codex", "sys.stderr.write('fallo'); sys.exit(3)"))
    r = codex.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_SALIO_CON_ERROR" and r["exit_code"] == 3 and r["efectos_posibles"] is True


def test_codex_timeout(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", fake(tmp_path, "codex", "import time; time.sleep(30)"))
    monkeypatch.setattr("agentes.adaptadores._comun.TIMEOUT_S", 0.5)
    r = codex.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_TIMEOUT" and r["efectos_posibles"] is True


def test_codex_sin_mensaje_final_no_es_exito(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", fake(tmp_path, "codex", "print('nada util')"))
    r = codex.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_SIN_RESULTADO" and r["efectos_posibles"] is True


def test_codex_entradas_invalidas_no_lanzan_nada(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_CODEX_BIN", fake(tmp_path, "codex", CODEX_OK))
    r = codex.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "hf/inventado"})
    assert r["ok"] is False and r["codigo"] == "MODELO_NO_REGISTRADO" and not (tmp_path / "codex.log").exists()


# ---------------- opencode ----------------
OPENCODE_OK = ("print(json.dumps({'type': 'tool_use', 'part': {'tool': 'read', 'state': {'status': 'completed'}}}))\n"
               "print(json.dumps({'type': 'text', 'part': {'type': 'text', 'text': 'revision hecha'}}))")


def test_opencode_camino_feliz_config_inline_y_permisos(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_OPENCODE_BIN", fake(tmp_path, "opencode", OPENCODE_OK))
    r = opencode.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "hf/qwen3.5-0.8b"})
    comunes_ok(r, "opencode")
    assert r["resultado"] == "revision hecha" and "read" in r["herramientas"]
    c = llamadas(tmp_path, "opencode")[0]
    a = c["argv"]
    assert a[:2] == ["run", "--format"] and a[2] == "json" and a[a.index("--dir") + 1] == os.path.realpath(str(tmp_path / "ws"))
    assert a[a.index("-m") + 1] == "riu/qwen3.5-0.8b" and "--auto" not in a
    cfg = json.loads(c["env"]["OPENCODE_CONFIG_CONTENT"])
    assert cfg["provider"]["riu"]["npm"] == "@ai-sdk/openai-compatible" and cfg["provider"]["riu"]["options"]["baseURL"] == "http://127.0.0.1:7870/v1"
    assert cfg["provider"]["riu"]["options"]["apiKey"] == "{env:RIU_AGENTE_LLM_KEY}" and "qwen3.5-0.8b" in cfg["provider"]["riu"]["models"]
    assert cfg["permission"]["edit"] == "deny" and cfg["permission"]["bash"] == "deny" and cfg["permission"]["webfetch"] == "deny"


def test_opencode_permisos_de_escritura_y_ejecucion(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_OPENCODE_BIN", fake(tmp_path, "opencode", OPENCODE_OK))
    opencode.run(permisos=permisos(tmp_path, escritura=True), **BASE)
    cfg = json.loads(llamadas(tmp_path, "opencode")[0]["env"]["OPENCODE_CONFIG_CONTENT"])
    assert cfg["permission"]["edit"] == "allow" and cfg["permission"]["bash"] == "deny"
    opencode.run(permisos=permisos(tmp_path, escritura=True, ejecucion=True), **BASE)
    cfg = json.loads(llamadas(tmp_path, "opencode")[1]["env"]["OPENCODE_CONFIG_CONTENT"])
    assert cfg["permission"]["bash"] == "allow"


def test_opencode_no_instalado_y_error(monkeypatch, tmp_path):
    r = opencode.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_INSTALADO"
    monkeypatch.setenv("RIU_OPENCODE_BIN", fake(tmp_path, "opencode", "sys.exit(1)"))
    r = opencode.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_SALIO_CON_ERROR"


# ---------------- swe-agent ----------------
SWE_OK = ("d = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--output_dir=')][0]\nos.makedirs(d + '/inst', exist_ok=True)\n"
          "open(d + '/inst/inst.patch', 'w').write('diff --git a/x b/x\\n+corregido\\n')\nopen(d + '/inst/inst.traj', 'w').write('{}')\nprint('SWE-agent terminado')")


def test_swe_agent_camino_feliz(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_SWEAGENT_BIN", fake(tmp_path, "sweagent", SWE_OK))
    monkeypatch.setenv("RIU_DOCKER_BIN", fake(tmp_path, "docker", "pass"))
    r = swe_agent.run(permisos=permisos(tmp_path), **BASE)
    comunes_ok(r, "swe-agent")
    assert "diff --git" in r["resultado"] and any(e.endswith(".patch") for e in r["evidencias"] if isinstance(e, str))
    c = llamadas(tmp_path, "sweagent")[0]
    a = c["argv"]
    assert a[0] == "run" and "--agent.model.name=openai/qwen2.5-coder-1.5b" in a and "--agent.model.api_base=http://127.0.0.1:7870/v1" in a
    assert "--agent.model.api_key=$RIU_AGENTE_LLM_KEY" in a and "--env.repo.path=%s" % os.path.realpath(str(tmp_path / "ws")) in a
    assert any(x.startswith("--problem_statement.text=Tarea t-1") and "corrige el bug" in x for x in a)
    assert "--agent.model.per_instance_cost_limit=0" in a and not any("deployment.type=local" in x for x in a)
    assert "RIU_API_KEY" not in c["env"]


def test_swe_agent_exige_docker(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_SWEAGENT_BIN", fake(tmp_path, "sweagent", SWE_OK))
    r = swe_agent.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_CONFIGURADO" and "Docker" in r["error"] and r["efectos_posibles"] is False
    assert not (tmp_path / "sweagent.log").exists()


def test_swe_agent_no_instalado_y_sin_trayectoria(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_DOCKER_BIN", fake(tmp_path, "docker", "pass"))
    r = swe_agent.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_INSTALADO"
    monkeypatch.setenv("RIU_SWEAGENT_BIN", fake(tmp_path, "sweagent", "print('sin archivos')"))
    r = swe_agent.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_SIN_RESULTADO"


# ---------------- openhands ----------------
OH_OK = ("if sys.argv[1:2] == ['-c']:\n    sys.exit(0)\n"
         "print('ruido previo')\nprint(json.dumps({'ok': True, 'resultado': 'tests verdes', 'estado': 'finished', 'herramientas': ['terminal'], 'eventos': 7}))")


def test_openhands_camino_feliz_via_sdk_en_subproceso(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", fake(tmp_path, "oh", OH_OK))
    r = openhands.run(permisos=permisos(tmp_path, escritura=True, ejecucion=True), **{**BASE, "modelo": "hf/lfm2.5-350m"})
    comunes_ok(r, "openhands")
    assert r["resultado"] == "tests verdes" and r["herramientas"] == ["terminal"]
    previa, ejec = llamadas(tmp_path, "oh")
    assert previa["argv"][0] == "-c" and "openhands.sdk" in previa["argv"][1]
    assert ejec["argv"][0].endswith("_openhands_runner.py")
    entrada = json.loads(ejec["stdin"])
    assert entrada["modelo"] == "openai/lfm2.5-350m" and entrada["base_url"] == "http://127.0.0.1:7870/v1" and entrada["ejecucion"] is True
    assert entrada["directorio"] == os.path.realpath(str(tmp_path / "ws")) and "corrige el bug" in entrada["prompt"] and "api_key" not in json.dumps(entrada)
    assert ejec["env"]["RIU_AGENTE_LLM_KEY"] == "no-requerida" and "RIU_API_KEY" not in ejec["env"]


def test_openhands_sdk_ausente(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", fake(tmp_path, "oh", "sys.exit(3)"))
    r = openhands.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_INSTALADO" and r["efectos_posibles"] is False and r["recibo"] is None
    assert len(llamadas(tmp_path, "oh")) == 1  # solo la comprobacion, no se ejecuto nada


def test_openhands_el_runner_reporta_error_o_estado_no_terminado(monkeypatch, tmp_path):
    cuerpo = "if sys.argv[1:2] == ['-c']:\n    sys.exit(0)\nprint(json.dumps({'ok': False, 'codigo': 'OPENHANDS_ESTADO', 'error': 'stuck', 'estado': 'stuck'}))"
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", fake(tmp_path, "oh", cuerpo))
    r = openhands.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "OPENHANDS_ESTADO" and r["efectos_posibles"] is True


def test_openhands_sin_json_del_runner(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", fake(tmp_path, "oh", "if sys.argv[1:2] == ['-c']:\n    sys.exit(0)\nprint('basura')"))
    r = openhands.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_SIN_RESULTADO"


# ---------------- claude-code ----------------
CC_OK = "print(json.dumps({'type': 'result', 'is_error': False, 'result': 'plan revisado', 'num_turns': 2, 'session_id': 's'}))"


def cfg_claude(monkeypatch, tmp_path, cuerpo=CC_OK):
    monkeypatch.setenv("RIU_CLAUDE_BIN", fake(tmp_path, "claude", cuerpo))
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_URL", "http://127.0.0.1:8082")
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_MODELO", "z-ai/glm-5.3")
    monkeypatch.setenv("NVIDIA_API_KEY", CLAVE_FICTICIA)


def test_claude_code_camino_feliz_lectura(monkeypatch, tmp_path):
    cfg_claude(monkeypatch, tmp_path)
    r = claude_code.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "nvidia/z-ai/glm-5.3"})
    comunes_ok(r, "claude-code")
    assert r["resultado"] == "plan revisado"
    c = llamadas(tmp_path, "claude")[0]
    a = c["argv"]
    assert a[0] == "-p" and a[a.index("--output-format") + 1] == "json" and "--no-session-persistence" in a
    assert a[a.index("--permission-mode") + 1] == "plan" and "--dangerously-skip-permissions" not in a
    assert a[a.index("--allowedTools") + 1] == "Read,Glob,Grep" and c["cwd"] == os.path.realpath(str(tmp_path / "ws"))
    assert c["env"]["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:8082" and "ANTHROPIC_API_KEY" not in c["env"] and "RIU_API_KEY" not in c["env"]
    assert CLAVE_FICTICIA not in " ".join(a) and "corrige el bug" in c["stdin"]


def test_claude_code_permisos(monkeypatch, tmp_path):
    cfg_claude(monkeypatch, tmp_path)
    m = {**BASE, "modelo": "nvidia/z-ai/glm-5.3"}
    claude_code.run(permisos=permisos(tmp_path, escritura=True), **m)
    claude_code.run(permisos=permisos(tmp_path, escritura=True, ejecucion=True, aprobado_por="ana"), **m)
    a1, a2 = (c["argv"] for c in llamadas(tmp_path, "claude"))
    assert a1[a1.index("--permission-mode") + 1] == "acceptEdits" and a1[a1.index("--allowedTools") + 1] == "Read,Glob,Grep,Edit,Write"
    t2 = a2[a2.index("--allowedTools") + 1].split(",")
    assert t2[:5] == ["Read", "Glob", "Grep", "Edit", "Write"] and "Bash" not in t2, "Bash sin patron = shell libre: no se concede"
    assert all(x.startswith("Bash(") and x.endswith(")") for x in t2[5:]) and "Bash(git status:*)" in t2 and "Bash(pytest:*)" in t2
    assert not any(re.search(r"git push|rm |curl|wget|sudo|git:\*|sh:\*|bash:\*", x) for x in t2)


def test_claude_code_modelo_incompatible_con_la_pasarela(monkeypatch, tmp_path):
    cfg_claude(monkeypatch, tmp_path)
    for modelo in ("hf/lfm2.5-350m", "groq/qwen/qwen3.8-27b", "nvidia/meta/muse-glimmer-30b"):
        r = claude_code.run(permisos=permisos(tmp_path), **{**BASE, "modelo": modelo})
        assert r["ok"] is False and r["codigo"] == "MODELO_INCOMPATIBLE" and r["efectos_posibles"] is False
    assert not (tmp_path / "claude.log").exists()


def test_claude_code_sin_pasarela_o_no_instalado(monkeypatch, tmp_path):
    r = claude_code.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "nvidia/z-ai/glm-5.3"})
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_INSTALADO"
    monkeypatch.setenv("RIU_CLAUDE_BIN", fake(tmp_path, "claude", CC_OK))
    r = claude_code.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "nvidia/z-ai/glm-5.3"})
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_CONFIGURADO" and not (tmp_path / "claude.log").exists()


def test_claude_code_is_error_no_es_exito(monkeypatch, tmp_path):
    cfg_claude(monkeypatch, tmp_path, "print(json.dumps({'type': 'result', 'is_error': True, 'result': 'API Error 401'}))")
    r = claude_code.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "nvidia/z-ai/glm-5.3"})
    assert r["ok"] is False and r["codigo"] == "AGENTE_REPORTO_ERROR" and r["efectos_posibles"] is True


# ---------------- openclaw (Gateway HTTP) ----------------
class Gateway(BaseHTTPRequestHandler):
    visto, estado, cuerpo = [], 200, {"id": "chatcmpl-1", "model": "openclaw/default", "choices": [{"message": {"role": "assistant", "content": "orquestado"}, "finish_reason": "stop"}]}

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        type(self).visto.append((self.path, dict(self.headers), json.loads(self.rfile.read(n))))
        self.send_response(type(self).estado)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(type(self).cuerpo).encode())

    def log_message(self, *a):
        pass


@pytest.fixture
def gateway(monkeypatch):
    Gateway.visto, Gateway.estado = [], 200
    s = HTTPServer(("127.0.0.1", 0), Gateway)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    monkeypatch.setenv("RIU_OPENCLAW_URL", "http://127.0.0.1:%d" % s.server_port)
    yield s
    s.shutdown(); s.server_close()


def test_openclaw_camino_feliz(monkeypatch, tmp_path, gateway):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    r = openclaw.run(permisos=permisos(tmp_path), **{**BASE, "modelo": "hf/lfm2.5-350m"})
    comunes_ok(r, "openclaw")
    assert r["resultado"] == "orquestado" and CLAVE_FICTICIA not in json.dumps(r)
    ruta, cab, cuerpo = Gateway.visto[0]
    cab = {k.lower(): v for k, v in cab.items()}
    assert ruta == "/v1/chat/completions" and cab["authorization"] == "Bearer " + CLAVE_FICTICIA and cab["x-openclaw-model"] == "swecode/lfm2.5-350m"
    assert cuerpo["model"] == "openclaw/default" and cuerpo["user"] == "conv:t-1" and "corrige el bug" in cuerpo["messages"][0]["content"]


def test_openclaw_gateway_caido_es_no_instalado(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    monkeypatch.setenv("RIU_OPENCLAW_URL", "http://127.0.0.1:9")
    r = openclaw.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_INSTALADO" and r["efectos_posibles"] is False and r["recibo"] is None


def test_openclaw_sin_token_no_llama(monkeypatch, tmp_path, gateway):
    r = openclaw.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "AGENTE_NO_CONFIGURADO" and Gateway.visto == []


@pytest.mark.parametrize("estado,codigo,efectos", [(401, "AGENTE_NO_CONFIGURADO", False), (404, "AGENTE_NO_CONFIGURADO", False), (500, "AGENTE_SALIO_CON_ERROR", True)])
def test_openclaw_errores_http(monkeypatch, tmp_path, gateway, estado, codigo, efectos):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    Gateway.estado = estado
    r = openclaw.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == codigo and r["efectos_posibles"] is efectos


def test_openclaw_rechaza_url_remota_sin_https(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    monkeypatch.setenv("RIU_OPENCLAW_URL", "http://ejemplo.invalid:18789")
    r = openclaw.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "OPENCLAW_URL_INVALIDA"


def test_openclaw_respuesta_sin_contenido_no_es_exito(monkeypatch, tmp_path, gateway):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    Gateway.cuerpo = {"choices": []}
    try:
        r = openclaw.run(permisos=permisos(tmp_path), **BASE)
    finally:
        Gateway.cuerpo = {"id": "chatcmpl-1", "model": "openclaw/default", "choices": [{"message": {"role": "assistant", "content": "orquestado"}, "finish_reason": "stop"}]}
    assert r["ok"] is False and r["codigo"] == "AGENTE_SIN_RESULTADO"


# ---------------- ninguna ejecucion falsa: sin software, todos fallan explicitamente ----------------
def test_los_seis_sin_software_devuelven_ok_false(tmp_path):
    mods = [codex, opencode, swe_agent, openhands, claude_code, openclaw]
    for m in mods:
        r = m.run(permisos=permisos(tmp_path), **BASE)
        assert r["ok"] is False and r["recibo"] is None and r["codigo"] in ("AGENTE_NO_INSTALADO", "AGENTE_NO_CONFIGURADO", "MODELO_INCOMPATIBLE"), (m.__name__, r)


# ---------------- hallazgos de auditoria: politicas de los adaptadores ----------------
def test_opencode_deniega_external_directory_siempre(monkeypatch, tmp_path):
    monkeypatch.setenv("RIU_OPENCODE_BIN", fake(tmp_path, "opencode", OPENCODE_OK))
    for kw in ({}, {"escritura": True}, {"escritura": True, "ejecucion": True}):
        opencode.run(permisos=permisos(tmp_path, **kw), **BASE)
    for c in llamadas(tmp_path, "opencode"):
        assert json.loads(c["env"]["OPENCODE_CONFIG_CONTENT"])["permission"]["external_directory"] == "deny"


def test_claude_code_ejecucion_exige_aprobacion_de_un_operador(monkeypatch, tmp_path):
    cfg_claude(monkeypatch, tmp_path)
    m = {**BASE, "modelo": "nvidia/z-ai/glm-5.3"}
    r = claude_code.run(permisos=permisos(tmp_path, escritura=True, ejecucion=True), **m)
    assert r["ok"] is False and r["codigo"] == "APROBACION_REQUERIDA" and r["efectos_posibles"] is False and not (tmp_path / "claude.log").exists()
    r = claude_code.run(permisos=permisos(tmp_path, ejecucion=True, aprobado_por=""), **m)
    assert r["ok"] is False and r["codigo"] == "APROBACION_REQUERIDA"


def test_claude_code_bash_ampliable_solo_por_el_operador_del_entorno(monkeypatch, tmp_path):
    cfg_claude(monkeypatch, tmp_path)
    monkeypatch.setenv("RIU_CLAUDE_BASH_PERMITIDOS", "make test, npm run lint")
    claude_code.run(permisos=permisos(tmp_path, ejecucion=True, aprobado_por="ana"), **{**BASE, "modelo": "nvidia/z-ai/glm-5.3"})
    a = llamadas(tmp_path, "claude")[0]["argv"]
    t = a[a.index("--allowedTools") + 1].split(",")
    assert "Bash(make test:*)" in t and "Bash(npm run lint:*)" in t and "Bash" not in t


def test_openclaw_tarea_de_solo_lectura_no_se_ejecuta_porque_el_gateway_no_lo_garantiza(monkeypatch, tmp_path, gateway):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    r = openclaw.run(permisos=permisos(tmp_path), **BASE)
    assert r["ok"] is False and r["codigo"] == "POLITICA_NO_GARANTIZADA" and r["efectos_posibles"] is False and r["recibo"] is None
    assert Gateway.visto == [], "el Gateway no recibio nada"
    r = openclaw.run(permisos=permisos(tmp_path, escritura=True), **BASE)  # con escritura/ejecucion aprobadas si corre (las politicas son las del Gateway)
    assert r["ok"] is True and len(Gateway.visto) == 1
    r = openclaw.run(permisos=permisos(tmp_path, ejecucion=True), **BASE)
    assert r["ok"] is True


def test_openclaw_solo_lectura_si_el_operador_declara_el_gateway_en_solo_lectura(monkeypatch, tmp_path, gateway):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    monkeypatch.setenv("RIU_OPENCLAW_GATEWAY_SOLO_LECTURA", "1")
    assert openclaw.run(permisos=permisos(tmp_path), **BASE)["ok"] is True


def test_openclaw_no_sigue_redirecciones(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", CLAVE_FICTICIA)
    destino_visto = []
    class Destino(BaseHTTPRequestHandler):
        def do_POST(self):
            destino_visto.append(dict(self.headers)); self.send_response(200); self.end_headers(); self.wfile.write(b"{}")
        def log_message(self, *a): pass
    d = HTTPServer(("127.0.0.1", 0), Destino)
    class Redir(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(307); self.send_header("Location", "http://127.0.0.1:%d/robo" % d.server_port); self.end_headers()
        def log_message(self, *a): pass
    o = HTTPServer(("127.0.0.1", 0), Redir)
    for s in (d, o): threading.Thread(target=s.serve_forever, daemon=True).start()
    monkeypatch.setenv("RIU_OPENCLAW_URL", "http://127.0.0.1:%d" % o.server_port)
    try:
        r = openclaw.run(permisos=permisos(tmp_path, escritura=True), **BASE)
    finally:
        for s in (d, o): s.shutdown(); s.server_close()
    assert r["ok"] is False and r["codigo"] == "REDIRECCION_NO_PERMITIDA" and r["efectos_posibles"] is False
    assert destino_visto == [], "el token no viajo al destino de la redireccion"
    assert CLAVE_FICTICIA not in json.dumps(r)
