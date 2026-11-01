"""Defaults del Harness y de los adaptadores para funcionar SIN variables nuevas en Hugging Face (solo si la variable NO esta definida; vacia = desactivada a proposito):
RIU_SWE_WORKSPACE_RAIZ (directorio privado 0700), SWECODE_URL_S1..S3 (URLs publicas), operadores derivados de los aprobadores, y el plan (objetivo + operaciones previstas)
que el Harness manda al bridge cuando ejecuta herramientas (confirmacion 141 activa por defecto en el bridge). Ninguna clave real; sin red."""
import json
import os
import stat
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plugins.deepseek_harness import server as h
from agentes.adaptadores import _comun, disponibilidad, workflows as wf

PUBLICAS = {"S1": "https://comand-center-1-swe-code-s1.hf.space/v1", "S2": "https://comand-center-1-swe-code-s2.hf.space/v1", "S3": "https://comand-center-1-swe-code-s3.hf.space/v1"}


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
    for v in ("RIU_SWE_WORKSPACE_RAIZ", "BRIDGE_STATE_DIR", "SWECODE_URL_S1", "SWECODE_URL_S2", "SWECODE_URL_S3", "RIU_SWE_OPERADORES", "RIU_SWE_APROBADORES", "BRIDGE_APROBADORES"):
        monkeypatch.delenv(v, raising=False)


# ---------------- RIU_SWE_WORKSPACE_RAIZ ----------------
def test_workspace_por_defecto_bajo_bridge_state_dir_con_permisos_0700(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_STATE_DIR", str(tmp_path / "estado"))
    (tmp_path / "estado").mkdir()
    h._defaults_entorno()
    raiz = os.environ["RIU_SWE_WORKSPACE_RAIZ"]
    assert raiz == str(tmp_path / "estado" / "swe-workspace") and os.path.isdir(raiz)
    assert stat.S_IMODE(os.stat(raiz).st_mode) == 0o700
    h._defaults_entorno()  # idempotente
    assert os.environ["RIU_SWE_WORKSPACE_RAIZ"] == raiz


def test_workspace_por_defecto_sin_bridge_state_dir_usa_el_tmp_del_sistema(monkeypatch, tmp_path):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    h._defaults_entorno()
    raiz = os.environ["RIU_SWE_WORKSPACE_RAIZ"]
    assert raiz == str(tmp_path / "swe-workspace") and stat.S_IMODE(os.stat(raiz).st_mode) == 0o700


def test_workspace_definido_no_se_toca_ni_vacio(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("RIU_SWE_WORKSPACE_RAIZ", "/mi/raiz")
    h._defaults_entorno()
    assert os.environ["RIU_SWE_WORKSPACE_RAIZ"] == "/mi/raiz" and not (tmp_path / "swe-workspace").exists()
    monkeypatch.setenv("RIU_SWE_WORKSPACE_RAIZ", "")
    h._defaults_entorno()
    assert os.environ["RIU_SWE_WORKSPACE_RAIZ"] == "", "vacia = desactivada a proposito"


def test_workspace_existente_con_permisos_abiertos_se_cierra_a_0700_y_un_enlace_simbolico_se_rechaza(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_STATE_DIR", str(tmp_path))
    d = tmp_path / "swe-workspace"; d.mkdir(); d.chmod(0o755)
    h._defaults_entorno()
    assert stat.S_IMODE(os.stat(d).st_mode) == 0o700 and os.environ["RIU_SWE_WORKSPACE_RAIZ"] == str(d)
    monkeypatch.delenv("RIU_SWE_WORKSPACE_RAIZ")
    d.rmdir(); (tmp_path / "otro").mkdir(); os.symlink(tmp_path / "otro", d)
    h._defaults_entorno()
    assert "RIU_SWE_WORKSPACE_RAIZ" not in os.environ, "un enlace simbolico no es un workspace seguro: queda sin configurar"


def test_workspace_que_no_se_puede_crear_queda_sin_configurar(monkeypatch, tmp_path):
    f = tmp_path / "archivo"; f.write_text("x")
    monkeypatch.setenv("BRIDGE_STATE_DIR", str(f))  # un archivo, no un directorio
    h._defaults_entorno()
    assert "RIU_SWE_WORKSPACE_RAIZ" not in os.environ


def test_carpeta_de_proyecto_se_crea_solo_bajo_la_raiz_por_defecto(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_STATE_DIR", str(tmp_path))
    h._defaults_entorno()
    ruta, falta = wf._directorio({"proyecto": "mi-proyecto"})
    assert falta is None and ruta == str(tmp_path / "swe-workspace" / "mi-proyecto") and stat.S_IMODE(os.stat(ruta).st_mode) == 0o700
    assert wf._directorio({"proyecto": "../fuera"})[1][0] == "PROYECTO_INVALIDO"
    explicita = tmp_path / "mia"; explicita.mkdir()
    monkeypatch.setenv("RIU_SWE_WORKSPACE_RAIZ", str(explicita))
    ruta, falta = wf._directorio({"proyecto": "nuevo"})
    assert ruta is None and falta[0] == "WORKSPACE_NO_CONFIGURADO" and not (explicita / "nuevo").exists(), "una raiz elegida por el operador sigue exigiendo que la carpeta exista"


def test_el_workspace_por_defecto_se_aplica_al_usar_las_herramientas_swe(monkeypatch, tmp_path):
    monkeypatch.setenv("BRIDGE_STATE_DIR", str(tmp_path))
    h._ctx_swe()
    assert os.environ["RIU_SWE_WORKSPACE_RAIZ"] == str(tmp_path / "swe-workspace")


# ---------------- SWECODE_URL_S1..S3 ----------------
def test_urls_swecode_publicas_solo_si_la_variable_no_esta(monkeypatch):
    assert _comun.SWECODE_URLS_PUBLICAS == PUBLICAS
    for s in PUBLICAS:
        assert _comun.url_swecode(s) == PUBLICAS[s]
    monkeypatch.setenv("SWECODE_URL_S1", " http://127.0.0.1:9101/v1 ")
    monkeypatch.setenv("SWECODE_URL_S2", "")
    assert _comun.url_swecode("S1") == "http://127.0.0.1:9101/v1" and _comun.url_swecode("S2") == "", "vacia = desactivada a proposito"
    assert _comun.url_swecode("S3") == PUBLICAS["S3"]
    with pytest.raises(ValueError):
        _comun.url_swecode("S4")


def test_disponibilidad_con_los_defaults_ve_los_servidores_hf_y_liquid_mirror(monkeypatch):
    assert disponibilidad._hf_urls() == [PUBLICAS["S1"], PUBLICAS["S2"], PUBLICAS["S3"]] and disponibilidad._hf_configurado()
    agentes = {"openhands": {"disponible": True, "motivo": ""}}
    assert disponibilidad._workflow_liquid_mirror(agentes)["disponible"] is True, "S2 y S3 publicas distintas: Liquid Mirror configurado sin variables"
    for s in ("S1", "S2", "S3"):
        monkeypatch.setenv("SWECODE_URL_" + s, "")
    assert disponibilidad._hf_urls() == [] and not disponibilidad._hf_configurado()
    assert disponibilidad._workflow_liquid_mirror(agentes)["disponible"] is False


def test_liquid_usa_las_urls_publicas_por_defecto_y_sigue_exigiendo_servidores_independientes(monkeypatch):
    assert wf._urls_liquid() == {"S2": PUBLICAS["S2"], "S3": PUBLICAS["S3"]}
    monkeypatch.setenv("SWECODE_URL_S3", PUBLICAS["S2"])
    with pytest.raises(ValueError, match="LIQUID_SERVIDORES_NO_INDEPENDIENTES"):
        wf._urls_liquid()
    monkeypatch.setenv("SWECODE_URL_S3", "")
    with pytest.raises(ValueError, match="LIQUID_SERVIDOR_NO_CONFIGURADO"):
        wf._urls_liquid()
    with pytest.raises(ValueError, match="LIQUID_SERVIDOR_NO_CONFIGURADO"):
        wf.llamar_servidor("S2", "hf/lfm2.5-350m", [{"role": "user", "content": "x"}])  # S3 vacia: con un solo servidor no hay independencia


# ---------------- operadores derivados de los aprobadores ----------------
H1, H2 = "a" * 64, "b" * 64


def test_operadores_se_derivan_de_los_aprobadores_si_no_hay_riu_swe_operadores(monkeypatch):
    assert wf._operadores_env() == set(), "sin nada configurado no hay operadores (no se inventa ninguno)"
    monkeypatch.setenv("RIU_SWE_APROBADORES", f"ana:{H1},malformada,x:corta")
    monkeypatch.setenv("BRIDGE_APROBADORES", f"luis:{H2},ana:{H2}")
    assert wf._operadores_env() == {"ana", "luis"}
    monkeypatch.setenv("RIU_SWE_OPERADORES", "solo-este")
    assert wf._operadores_env() == {"solo-este"}, "RIU_SWE_OPERADORES, si esta, manda"
    monkeypatch.setenv("RIU_SWE_OPERADORES", "")
    assert wf._operadores_env() == set(), "vacia = a proposito ninguno"


# ---------------- plan hacia el bridge (confirmacion 141 por defecto) ----------------
def _bridge_captura():
    vistos = []
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            vistos.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}]}).encode())
        def log_message(self, *a): pass
    s = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_port, vistos


def test_bridge_chat_con_tools_y_tarea_manda_objetivo_y_operaciones_previstas(monkeypatch):
    s, url, vistos = _bridge_captura()
    tools = [{"type": "function", "function": {"name": "github_leer"}}, {"type": "function", "function": {"name": "almacen"}}]
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "lee el repositorio y resume " + "x" * 3000}]
    try:
        with patch.dict(os.environ, {"RIU_SWE_BRIDGE_URL": url}):
            h._bridge_chat(msgs, "groq/qwen/qwen3.8-27b", "tarea-9", {"tools": tools, "tool_choice": "auto"})
            h._bridge_chat(msgs, "groq/qwen/qwen3.8-27b", "tarea-9", {})
            h._bridge_chat(msgs, "groq/qwen/qwen3.8-27b", "", {"tools": tools})
    finally:
        s.shutdown()
    con, sin_tools, sin_tarea = vistos
    assert con["operaciones_previstas"] == ["github_leer", "almacen"] and con["objetivo"].startswith("lee el repositorio y resume") and 0 < len(con["objetivo"]) <= 500
    assert "objetivo" not in sin_tools and "operaciones_previstas" not in sin_tools, "sin tools no hay efectos: no se manda plan"
    assert "objetivo" not in sin_tarea, "sin tarea no hay checkpoint ni plan"
