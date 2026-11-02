"""Disponibilidad real para result.swe del `status` del Harness: instalado/configurado segun lo que exige cada adaptador, SIN ejecutar nada con efectos
(los binarios falsos de estas pruebas dejan una marca si alguien los lanza) y sin revelar claves. Ninguna clave real."""
import json
import os
import stat
import sys

import pytest

from agentes.adaptadores import disponibilidad, modelos

VARS = ["RIU_CODEX_BIN", "RIU_CODEX_BASE_URL", "RIU_OPENCODE_BIN", "RIU_SWEAGENT_BIN", "RIU_DOCKER_BIN", "RIU_OPENHANDS_PYTHON", "RIU_CLAUDE_BIN",
        "RIU_CLAUDE_PASARELA_URL", "RIU_CLAUDE_PASARELA_MODELO", "RIU_OPENCLAW_URL", "OPENCLAW_GATEWAY_TOKEN", "SWECODE_URL_S1", "SWECODE_URL_S2", "SWECODE_URL_S3",
        "RIU_SWE_SONDA_MODELOS"] + ["%s_API_KEY%s" % (p, s) for p in ("GROQ", "NVIDIA") for s in [""] + ["_%d" % i for i in range(1, 21)]]
CLAVE_GROQ, CLAVE_NVIDIA = "gsk_clave-falsa-de-prueba-1234567890", "nvapi-clave-falsa-de-prueba-1234567890"


@pytest.fixture
def vacio(monkeypatch, tmp_path):
    for v in VARS:
        monkeypatch.delenv(v, raising=False)
    for s in ("S1", "S2", "S3"):  # sin variable ahora rigen las URLs publicas por defecto (_comun.url_swecode): vacia = "sin servidor configurado"
        monkeypatch.setenv("SWECODE_URL_" + s, "")
    monkeypatch.setenv("PATH", str(tmp_path / "sin-binarios"))  # ni claude ni docker del sistema
    monkeypatch.setenv("RIU_SWE_SONDA_MODELOS", "0")
    return tmp_path


def falso(tmp_path, nombre):
    """Ejecutable que, si se LANZA, deja <nombre>.lanzado: la disponibilidad solo mira que exista, nunca lo ejecuta."""
    p = tmp_path / nombre
    p.write_text("#!%s\nopen(%r, 'w').write('lanzado')\n" % (sys.executable, str(tmp_path / (nombre + ".lanzado"))))
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def nunca_lanzado(tmp_path):
    return not list(tmp_path.glob("*.lanzado"))


def cap(**k):
    k.setdefault("sonda_openhands", lambda py: False)
    k.setdefault("sonda_gateway", lambda url: False)
    k.setdefault("sonda_hf", lambda url: True)
    return disponibilidad.capacidades(**k)


def viejo(e):
    """El contrato antiguo ({disponible, motivo}) sigue intacto; los campos nuevos (estado, veredicto, ...) se prueban en test_adaptadores_disponibilidad_estados.py."""
    return {"disponible": e["disponible"], "motivo": e["motivo"]}


def test_formato_exacto_y_claves_del_catalogo(vacio):
    c = cap()
    assert set(c) == {"agentes", "workflows", "modelos"}
    assert set(c["agentes"]) == set(modelos.AGENTES) and set(c["workflows"]) == set(modelos.WORKFLOWS) and set(c["modelos"]) == set(modelos.MODELOS)
    for grupo in c.values():
        for e in grupo.values():
            assert type(e["disponible"]) is bool and isinstance(e["motivo"], str)
    assert json.loads(json.dumps(c)) == c


def test_entorno_vacio_nada_conectado_salvo_individual(vacio):
    c = cap()
    assert all(e["disponible"] is False and e["motivo"] for e in c["agentes"].values())
    assert viejo(c["workflows"]["individual"]) == {"disponible": True, "motivo": ""}
    assert c["workflows"]["swe_code"]["disponible"] is False and c["workflows"]["liquid_mirror"]["disponible"] is False
    assert all(e["disponible"] is False and e["motivo"] for e in c["modelos"].values())


def test_codex_exige_binario_y_endpoint_responses(vacio, monkeypatch):
    monkeypatch.setenv("RIU_CODEX_BIN", falso(vacio, "codex"))
    e = cap()["agentes"]["codex"]
    assert e["disponible"] is False and "RIU_CODEX_BASE_URL" in e["motivo"]
    monkeypatch.setenv("RIU_CODEX_BASE_URL", "http://127.0.0.1:9999/v1")
    assert viejo(cap()["agentes"]["codex"]) == {"disponible": True, "motivo": ""}
    monkeypatch.setenv("RIU_CODEX_BIN", str(vacio / "no-existe"))
    e = cap()["agentes"]["codex"]
    assert e["disponible"] is False and "no esta instalado" in e["motivo"]
    assert nunca_lanzado(vacio)


def test_codex_con_bridge_existente_no_exige_url_adicional(vacio, monkeypatch):
    monkeypatch.setenv("RIU_CODEX_BIN", falso(vacio, "codex"))
    monkeypatch.setenv("RIU_API_KEY", "clave-ficticia-del-chat")
    monkeypatch.delenv("RIU_CODEX_BASE_URL", raising=False)
    assert cap(sonda_gateway=lambda url: True)["agentes"]["codex"]["estado"] == "DISPONIBLE"
    assert cap(sonda_gateway=lambda url: False)["agentes"]["codex"]["estado"] == "SIN VERIFICAR"
    assert nunca_lanzado(vacio)


def test_modelos_consultan_bridge_cuando_claves_viven_en_banco(vacio, monkeypatch):
    from unittest.mock import patch
    monkeypatch.setenv("RIU_API_KEY", "clave-ficticia-del-chat")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    lista = {"groq/qwen/qwen3.8-27b": {"disponible": True},
             "nvidia/z-ai/glm-5.3": {"disponible": None}}
    with patch.object(disponibilidad, "_modelos_bridge", return_value=lista) as probe:
        c = cap()["modelos"]
        assert c["groq/qwen/qwen3.8-27b"]["estado"] == "DISPONIBLE"
        assert c["nvidia/z-ai/glm-5.3"]["estado"] == "SIN VERIFICAR"
        assert probe.call_count == 1


def test_opencode_y_swe_agent(vacio, monkeypatch):
    monkeypatch.setenv("RIU_OPENCODE_BIN", falso(vacio, "opencode"))
    monkeypatch.setenv("RIU_SWEAGENT_BIN", falso(vacio, "sweagent"))
    c = cap()["agentes"]
    assert c["opencode"]["disponible"] is True
    assert c["swe-agent"]["disponible"] is False and "Docker" in c["swe-agent"]["motivo"]  # SWE-agent corre en contenedor
    monkeypatch.setenv("RIU_DOCKER_BIN", falso(vacio, "docker"))
    assert cap()["agentes"]["swe-agent"]["disponible"] is True
    assert nunca_lanzado(vacio)


def test_openhands_solo_si_el_python_importa_el_sdk(vacio, monkeypatch):
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", sys.executable)
    visto = []
    sonda = lambda py: visto.append(py) or False
    e = cap(sonda_openhands=sonda)["agentes"]["openhands"]
    assert e["disponible"] is False and "openhands.sdk" in e["motivo"] and visto == [sys.executable]
    assert viejo(cap(sonda_openhands=lambda py: True)["agentes"]["openhands"]) == {"disponible": True, "motivo": ""}
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", str(vacio / "no-existe"))
    assert cap(sonda_openhands=lambda py: pytest.fail("no se sondea un Python inexistente"))["agentes"]["openhands"]["disponible"] is False


def test_sonda_real_de_openhands_es_solo_importar_y_no_lanza_agentes(vacio, monkeypatch):
    assert disponibilidad._sonda_openhands(sys.executable) is False  # este Python no tiene el SDK
    assert disponibilidad._sonda_openhands(str(vacio / "no-existe")) is False


def test_claude_code_instalado_pero_sin_pasarela_no_esta_conectado(vacio, monkeypatch):
    monkeypatch.setenv("RIU_CLAUDE_BIN", falso(vacio, "claude"))
    e = cap()["agentes"]["claude-code"]
    assert e["disponible"] is False and "RIU_CLAUDE_PASARELA_URL" in e["motivo"] and "instalado" in e["motivo"]
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_URL", "http://127.0.0.1:8082")
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_MODELO", "minimaxai/minimax-m3.1-flash")
    e = cap()["agentes"]["claude-code"]
    assert e["disponible"] is True and e["modelos"] == ["nvidia/minimaxai/minimax-m3.1-flash"]  # solo el modelo NVIDIA que sirve la pasarela
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_MODELO", "modelo/fuera-del-catalogo")
    e = cap()["agentes"]["claude-code"]
    assert e["disponible"] is False and "catalogo" in e["motivo"]
    assert nunca_lanzado(vacio)


def test_openclaw_exige_token_url_valida_y_gateway_vivo(vacio, monkeypatch):
    assert "OPENCLAW_GATEWAY_TOKEN" in cap()["agentes"]["openclaw"]["motivo"]
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "token-falso-de-prueba")
    vistas = []
    e = cap(sonda_gateway=lambda u: vistas.append(u) or False)["agentes"]["openclaw"]
    assert e["disponible"] is False and "Gateway" in e["motivo"] and vistas == ["http://127.0.0.1:18789"]
    assert viejo(cap(sonda_gateway=lambda u: True)["agentes"]["openclaw"]) == {"disponible": True, "motivo": ""}
    monkeypatch.setenv("RIU_OPENCLAW_URL", "http://servidor-publico.example")  # http solo en loopback
    e = cap(sonda_gateway=lambda u: pytest.fail("URL invalida: no se sondea"))["agentes"]["openclaw"]
    assert e["disponible"] is False and "RIU_OPENCLAW_URL" in e["motivo"]
    assert "token-falso" not in json.dumps(cap())


def test_modelos_hf_segun_los_servidores_configurados(vacio, monkeypatch):
    hf = [m for m in modelos.MODELOS if m.startswith("hf/")]
    assert len(hf) == 4 and all("SWECODE_URL_S1..S3" in cap()["modelos"][m]["motivo"] for m in hf)
    monkeypatch.setenv("SWECODE_URL_S1", "http://127.0.0.1:9101/v1")
    c = cap(sonda_modelos=lambda p, k: set())  # con la verificacion activa y el servidor HF alcanzable (sonda_hf=True)
    assert all(c["modelos"][m]["estado"] == "SIN VERIFICAR" and c["modelos"][m]["intentable"] is True
               and c["modelos"][m]["causa"] == "modelo_hf_no_verificado" for m in hf)  # TCP no prueba inferencia
    assert c["workflows"]["liquid_mirror"]["disponible"] is False and "S2" in c["workflows"]["liquid_mirror"]["motivo"]  # Liquid Mirror necesita S2 y S3 propios


def test_liquid_mirror_exige_s2_y_s3_distintos_validos_y_el_verificador(vacio, monkeypatch):
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9102/v1")
    monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9102/v1")
    w = cap(sonda_openhands=lambda py: True)["workflows"]["liquid_mirror"]
    assert w["disponible"] is False and "independientes" in w["motivo"]
    monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9103/v1")
    w = cap(sonda_openhands=lambda py: False)["workflows"]["liquid_mirror"]
    assert w["disponible"] is False and "openhands" in w["motivo"]  # el verificador es OpenHands
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", sys.executable)
    assert viejo(cap(sonda_openhands=lambda py: True)["workflows"]["liquid_mirror"]) == {"disponible": True, "motivo": ""}
    monkeypatch.setenv("SWECODE_URL_S3", "http://publico.example/v1")
    assert cap(sonda_openhands=lambda py: True)["workflows"]["liquid_mirror"]["disponible"] is False


def test_swe_code_exige_codex_opencode_openhands_y_los_hf(vacio, monkeypatch):
    monkeypatch.setenv("RIU_CODEX_BIN", falso(vacio, "codex")); monkeypatch.setenv("RIU_CODEX_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("RIU_OPENCODE_BIN", falso(vacio, "opencode")); monkeypatch.setenv("RIU_OPENHANDS_PYTHON", sys.executable)
    w = cap(sonda_openhands=lambda py: True)["workflows"]["swe_code"]
    assert w["disponible"] is False and "SWECODE_URL_S1..S3" in w["motivo"]
    monkeypatch.setenv("SWECODE_URL_S1", "http://127.0.0.1:9101/v1")
    assert viejo(cap(sonda_openhands=lambda py: True)["workflows"]["swe_code"]) == {"disponible": True, "motivo": ""}
    w = cap(sonda_openhands=lambda py: False)["workflows"]["swe_code"]
    assert w["disponible"] is False and "openhands" in w["motivo"]
    assert nunca_lanzado(vacio)


def test_groq_y_nvidia_segun_claves_sin_revelarlas(vacio, monkeypatch):
    ext = [m for m in modelos.MODELOS if not m.startswith("hf/")]
    assert len(ext) == 5
    assert "GROQ_API_KEY" in cap()["modelos"]["groq/qwen/qwen3.8-27b"]["motivo"] and "NVIDIA_API_KEY" in cap()["modelos"]["nvidia/z-ai/glm-5.3"]["motivo"]
    monkeypatch.setenv("GROQ_API_KEY_3", CLAVE_GROQ)
    monkeypatch.setenv("NVIDIA_API_KEY", CLAVE_NVIDIA)
    c = cap()  # R6: clave presente + verificacion desactivada = SIN VERIFICAR, NO disponible (38)
    assert all(c["modelos"][m]["disponible"] is False and c["modelos"][m]["estado"] == "SIN VERIFICAR" for m in ext)
    c = cap(sonda_modelos=lambda p, k: {m["model"] for m in modelos.MODELOS.values() if m["provider"] == p})
    assert all(c["modelos"][m]["disponible"] is True for m in ext)
    volcado = json.dumps(c)
    assert CLAVE_GROQ not in volcado and CLAVE_NVIDIA not in volcado and "gsk_" not in volcado and "nvapi-" not in volcado


def test_get_models_del_proveedor_marca_lo_que_no_figura(vacio, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", CLAVE_GROQ); monkeypatch.setenv("NVIDIA_API_KEY", CLAVE_NVIDIA)
    pedidos = []
    def sonda(proveedor, clave):
        pedidos.append(proveedor)
        return {"groq": {"llama-3.3-70b-versatile"}, "nvidia": {"minimaxai/minimax-m3.1-flash", "z-ai/glm-5.3"}}[proveedor]
    c = cap(sonda_modelos=sonda)["modelos"]
    assert sorted(set(pedidos)) == ["groq", "nvidia"] and len(pedidos) == 2  # una consulta por proveedor
    assert c["groq/qwen/qwen3.8-27b"]["disponible"] is False and "GET /models" in c["groq/qwen/qwen3.8-27b"]["motivo"]
    assert c["nvidia/minimaxai/minimax-m3.1-flash"]["disponible"] is True and c["nvidia/z-ai/glm-5.3"]["disponible"] is True
    assert c["nvidia/meta/muse-glimmer-30b"]["disponible"] is False and "GET /models" in c["nvidia/meta/muse-glimmer-30b"]["motivo"]
    assert CLAVE_GROQ not in json.dumps(c) and CLAVE_NVIDIA not in json.dumps(c)


def test_si_el_proveedor_no_responde_no_se_inventa_ni_se_marca_caido(vacio, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", CLAVE_GROQ)
    def sonda(proveedor, clave):
        raise OSError("sin red " + clave)
    e = cap(sonda_modelos=sonda)["modelos"]["groq/qwen/qwen3.8-27b"]
    assert e["disponible"] is False and e["estado"] == "SIN VERIFICAR" and "sin verificar" in e["motivo"] and CLAVE_GROQ not in json.dumps(e)  # R6: un error del proveedor NUNCA es DISPONIBLE


def test_la_sonda_real_pide_get_models_con_la_clave_y_no_la_devuelve(vacio, monkeypatch):
    peticiones = []
    class R:
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def read(s, n=-1): return json.dumps({"data": [{"id": "qwen/qwen3.8-27b"}, {"id": "otro"}]}).encode()
    def abrir(req, timeout=0):
        peticiones.append((req.full_url, req.get_header("Authorization"), req.get_method(), timeout))
        return R()
    monkeypatch.setattr(disponibilidad._comun, "abrir", abrir)
    disponibilidad._CACHE.clear()
    assert disponibilidad._sonda_modelos("groq", CLAVE_GROQ) == {"qwen/qwen3.8-27b", "otro"}
    assert peticiones == [("https://api.groq.com/openai/v1/models", "Bearer " + CLAVE_GROQ, "GET", 5)]
    assert disponibilidad._sonda_modelos("groq", CLAVE_GROQ) == {"qwen/qwen3.8-27b", "otro"} and len(peticiones) == 1  # cache
    monkeypatch.setenv("GROQ_API_KEY", CLAVE_GROQ)
    monkeypatch.delenv("RIU_SWE_SONDA_MODELOS")
    disponibilidad._CACHE.clear()
    c = disponibilidad.capacidades(sonda_openhands=lambda p: False, sonda_gateway=lambda u: False)
    assert c["modelos"]["groq/qwen/qwen3.8-27b"]["disponible"] is True


def test_capacidades_nunca_lanza_un_agente(vacio, monkeypatch):
    for var, n in (("RIU_CODEX_BIN", "codex"), ("RIU_OPENCODE_BIN", "opencode"), ("RIU_SWEAGENT_BIN", "sweagent"), ("RIU_DOCKER_BIN", "docker"), ("RIU_CLAUDE_BIN", "claude")):
        monkeypatch.setenv(var, falso(vacio, n))
    monkeypatch.setenv("RIU_CODEX_BASE_URL", "http://127.0.0.1:9/v1")
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_URL", "http://127.0.0.1:8082"); monkeypatch.setenv("RIU_CLAUDE_PASARELA_MODELO", "z-ai/glm-5.3")
    c = cap()
    assert {a for a, e in c["agentes"].items() if e["disponible"]} == {"swe-agent", "opencode", "codex", "claude-code"}
    assert nunca_lanzado(vacio)


def test_cache_get_models_aislada_por_clave_y_rechazo_401(monkeypatch):
    """Dos claves del MISMO proveedor no heredan modelos ni permisos; un 401 cacheado mantiene su tipo."""
    llamadas = []
    class Respuesta:
        def __init__(self, modelos): self.modelos = modelos
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, n=-1): return json.dumps({"data": [{"id": m} for m in self.modelos]}).encode()
    def abrir(req, timeout=5):
        auth = req.get_header("Authorization")
        llamadas.append(auth)
        if auth == "Bearer clave-rechazada":
            raise disponibilidad.urllib.error.HTTPError(req.full_url, 401, "sin permiso", {}, None)
        return Respuesta(["modelo-uno"] if auth == "Bearer clave-uno" else ["modelo-dos"])
    monkeypatch.setattr(disponibilidad._comun, "abrir", abrir)
    disponibilidad._CACHE.clear()
    assert disponibilidad._sonda_modelos("groq", "clave-uno") == {"modelo-uno"}
    assert disponibilidad._sonda_modelos("groq", "clave-dos") == {"modelo-dos"}
    assert disponibilidad._sonda_modelos("groq", "clave-uno") == {"modelo-uno"}
    for intento in range(2):
        with pytest.raises(disponibilidad.ProveedorRechazo) as fallo:
            disponibilidad._sonda_modelos("groq", "clave-rechazada")
        assert fallo.value.codigo == 401
    assert llamadas == ["Bearer clave-uno", "Bearer clave-dos", "Bearer clave-rechazada"]
    assert all("clave-" not in str(k) for k in disponibilidad._CACHE)


def test_sonda_modelos_usa_apertura_sin_redirecciones(monkeypatch):
    """No reenviar Authorization a una URL redirigida: usa el abridor sin redirects compartido con los agentes."""
    vistos = []
    class R:
        def __enter__(s): return s
        def __exit__(s, *exc): return False
        def read(s, n=-1): return b'{"data":[{"id":"qwen/qwen3.8-27b"}]}'
    def seguro(req, timeout):
        vistos.append((req.full_url, req.get_header("Authorization")))
        return R()
    monkeypatch.setattr(disponibilidad._comun, "abrir", seguro)
    disponibilidad._CACHE.clear()
    assert disponibilidad._sonda_modelos("groq", "clave-de-prueba-no-real") == {"qwen/qwen3.8-27b"}
    assert vistos == [("https://api.groq.com/openai/v1/models", "Bearer clave-de-prueba-no-real")]
