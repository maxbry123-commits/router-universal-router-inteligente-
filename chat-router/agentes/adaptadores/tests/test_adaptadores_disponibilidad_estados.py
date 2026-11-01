"""R6 (auditoria GPT) e instrucciones 37/38/44/45/48/49/149/168/169: tres veredictos (DISPONIBLE / NO DISPONIBLE / SIN VERIFICAR) y los seis estados
(DISPONIBLE, NO INSTALADO, NO CONFIGURADO, NO COMPATIBLE, NO DISPONIBLE EN PROVEEDOR, SIN VERIFICAR). Un error de consulta del proveedor NUNCA produce DISPONIBLE.
Los campos antiguos `disponible` (bool) y `motivo` (str) se conservan; los nuevos son `estado`, `veredicto`, `verificado`, `causa`, `intentable` (+ `nombre`, `proveedor`, `nota` en modelos).
Claves FALSAS; nada se lanza ni sale a la red."""
import json
import os
import stat
import sys

import pytest

from agentes.adaptadores import disponibilidad, modelos

ESTADOS = {"DISPONIBLE", "NO INSTALADO", "NO CONFIGURADO", "NO COMPATIBLE", "NO DISPONIBLE EN PROVEEDOR", "SIN VERIFICAR"}
VARS = ["RIU_CODEX_BIN", "RIU_CODEX_BASE_URL", "RIU_OPENCODE_BIN", "RIU_SWEAGENT_BIN", "RIU_DOCKER_BIN", "RIU_OPENHANDS_PYTHON", "RIU_CLAUDE_BIN",
        "RIU_CLAUDE_PASARELA_URL", "RIU_CLAUDE_PASARELA_MODELO", "RIU_OPENCLAW_URL", "OPENCLAW_GATEWAY_TOKEN", "SWECODE_URL_S1", "SWECODE_URL_S2", "SWECODE_URL_S3",
        "RIU_SWE_SONDA_MODELOS"] + ["%s_API_KEY%s" % (p, s) for p in ("GROQ", "NVIDIA") for s in [""] + ["_%d" % i for i in range(1, 21)]]
CG, CN = "gsk_clave-falsa-de-prueba-1234567890", "nvapi-clave-falsa-de-prueba-1234567890"


@pytest.fixture
def vacio(monkeypatch, tmp_path):
    for v in VARS:
        monkeypatch.delenv(v, raising=False)
    for s in ("S1", "S2", "S3"):  # sin variable ahora rigen las URLs publicas por defecto (_comun.url_swecode): vacia = "sin servidor configurado"
        monkeypatch.setenv("SWECODE_URL_" + s, "")
    monkeypatch.setenv("PATH", str(tmp_path / "sin-binarios"))
    return tmp_path


def falso(tmp_path, nombre):
    p = tmp_path / nombre
    p.write_text("#!%s\npass\n" % sys.executable)
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def cap(**k):
    k.setdefault("sonda_openhands", lambda py: False)
    k.setdefault("sonda_gateway", lambda url: False)
    k.setdefault("sonda_hf", lambda url: False)
    return disponibilidad.capacidades(**k)


def test_cada_entrada_trae_estado_veredicto_verificado_y_causa_coherentes(vacio, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", CG)
    c = cap(sonda_modelos=lambda p, k: {"qwen/qwen3.8-27b"})
    for grupo in c.values():
        for e in grupo.values():
            assert e["estado"] in ESTADOS and type(e["disponible"]) is bool and isinstance(e["motivo"], str) and isinstance(e["causa"], str)
            assert e["disponible"] == (e["estado"] == "DISPONIBLE")
            assert e["veredicto"] == ("DISPONIBLE" if e["estado"] == "DISPONIBLE" else "SIN VERIFICAR" if e["estado"] == "SIN VERIFICAR" else "NO DISPONIBLE")
            assert e["verificado"] is (e["estado"] != "SIN VERIFICAR")
    assert json.loads(json.dumps(c)) == c


def test_error_de_consulta_del_proveedor_nunca_es_disponible(vacio, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", CG); monkeypatch.setenv("NVIDIA_API_KEY", CN)
    def rota(proveedor, clave):
        raise OSError("sin red " + clave)
    c = cap(sonda_modelos=rota)["modelos"]
    for mid in modelos.MODELOS:
        if mid.startswith("hf/"):
            continue
        e = c[mid]
        assert e["disponible"] is False and e["estado"] == "SIN VERIFICAR" and e["veredicto"] == "SIN VERIFICAR" and e["verificado"] is False, mid
        assert e["causa"] == "get_models_fallo" and e["intentable"] is True  # se puede intentar y mostrar el estado real; no se afirma que funcione
        assert CG not in json.dumps(e) and CN not in json.dumps(e)


def test_clave_presente_sin_verificar_no_es_disponible(vacio, monkeypatch):
    """38: una clave existente no es un modelo realmente disponible."""
    monkeypatch.setenv("GROQ_API_KEY", CG); monkeypatch.setenv("RIU_SWE_SONDA_MODELOS", "0")
    e = cap()["modelos"]["groq/qwen/qwen3.8-27b"]
    assert (e["estado"], e["disponible"], e["causa"]) == ("SIN VERIFICAR", False, "verificacion_desactivada")


def test_sin_clave_es_no_configurado_y_modelo_ausente_del_listado_es_no_disponible_en_proveedor(vacio, monkeypatch):
    c = cap(sonda_modelos=lambda p, k: set())["modelos"]
    assert c["groq/qwen/qwen3.8-27b"]["estado"] == "NO CONFIGURADO" and "GROQ_API_KEY" in c["groq/qwen/qwen3.8-27b"]["motivo"]
    monkeypatch.setenv("NVIDIA_API_KEY", CN)
    c = cap(sonda_modelos=lambda p, k: {"minimaxai/minimax-m3.1-flash"})["modelos"]
    assert c["nvidia/minimaxai/minimax-m3.1-flash"]["estado"] == "DISPONIBLE"
    glm = c["nvidia/z-ai/glm-5.3"]
    assert glm["estado"] == "NO DISPONIBLE EN PROVEEDOR" and glm["disponible"] is False and glm["intentable"] is False and glm["causa"] == "ausente_en_get_models"
    assert "404" in glm["nota"] and "build.nvidia.com/z-ai/glm-5.3" in glm["nota"]  # 168: GLM-5.3 sigue deshabilitado mientras el proveedor no lo liste


def test_glm_53_solo_se_habilita_si_el_proveedor_lo_lista(vacio, monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", CN)
    assert cap(sonda_modelos=lambda p, k: {"z-ai/glm-5.3"})["modelos"]["nvidia/z-ai/glm-5.3"]["estado"] == "DISPONIBLE"
    def rota(p, k):
        raise OSError("x")
    assert cap(sonda_modelos=rota)["modelos"]["nvidia/z-ai/glm-5.3"]["estado"] == "SIN VERIFICAR"  # nunca se activa por defecto


def test_clave_rechazada_por_el_proveedor_se_distingue(vacio, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", CG)
    def sonda(p, k):
        raise disponibilidad.ProveedorRechazo(401)
    e = cap(sonda_modelos=sonda)["modelos"]["groq/qwen/qwen3.8-27b"]
    assert e["estado"] == "SIN VERIFICAR" and e["causa"] == "clave_rechazada" and "401" in e["motivo"] and CG not in json.dumps(e)


def test_hf_estados_segun_servidor_configurado_y_alcanzable(vacio, monkeypatch):
    hf = [m for m in modelos.MODELOS if m.startswith("hf/")]
    c = cap()["modelos"]
    assert all(c[m]["estado"] == "NO CONFIGURADO" for m in hf)
    monkeypatch.setenv("SWECODE_URL_S1", "http://127.0.0.1:9101/v1")
    c = cap(sonda_hf=lambda u: False)["modelos"]
    assert all(c[m]["estado"] == "SIN VERIFICAR" and c[m]["causa"] == "servidor_hf_sin_respuesta" for m in hf)  # un Space dormido no es "no instalado"
    visto = []
    c = cap(sonda_hf=lambda u: visto.append(u) or True)["modelos"]
    assert all(c[m]["estado"] == "SIN VERIFICAR" and c[m]["intentable"] is True
               and c[m]["causa"] == "modelo_hf_no_verificado" for m in hf) and visto == ["http://127.0.0.1:9101/v1"]


def test_agentes_seis_estados(vacio, monkeypatch):
    c = cap()["agentes"]
    assert c["codex"]["estado"] == "NO INSTALADO" and c["opencode"]["estado"] == "NO INSTALADO" and c["swe-agent"]["estado"] == "NO INSTALADO"
    assert c["claude-code"]["estado"] == "NO INSTALADO" and c["openhands"]["estado"] == "NO INSTALADO"
    assert c["openclaw"]["estado"] == "NO CONFIGURADO"
    monkeypatch.setenv("RIU_CODEX_BIN", falso(vacio, "codex"))
    assert cap()["agentes"]["codex"]["estado"] == "NO CONFIGURADO"  # instalado pero sin endpoint /responses
    monkeypatch.setenv("RIU_SWEAGENT_BIN", falso(vacio, "sweagent"))
    assert cap()["agentes"]["swe-agent"]["estado"] == "NO CONFIGURADO" and "Docker" in cap()["agentes"]["swe-agent"]["motivo"]
    monkeypatch.setenv("RIU_CLAUDE_BIN", falso(vacio, "claude"))
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_URL", "http://127.0.0.1:8082")
    monkeypatch.setenv("RIU_CLAUDE_PASARELA_MODELO", "modelo/fuera-del-catalogo")
    e = cap()["agentes"]["claude-code"]
    assert e["estado"] == "NO COMPATIBLE" and e["disponible"] is False


def test_fallo_de_la_comprobacion_no_es_no_instalado(vacio, monkeypatch):
    """48/49: si la comprobacion simplemente fallo, SIN VERIFICAR (no NO INSTALADO)."""
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", sys.executable)
    assert cap(sonda_openhands=lambda py: None)["agentes"]["openhands"]["estado"] == "SIN VERIFICAR"
    assert cap(sonda_openhands=lambda py: False)["agentes"]["openhands"]["estado"] == "NO INSTALADO"
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "token-falso")
    e = cap(sonda_gateway=lambda u: False)["agentes"]["openclaw"]
    assert e["estado"] == "SIN VERIFICAR" and e["causa"] == "gateway_sin_respuesta"
    monkeypatch.setattr(disponibilidad, "_AGENTES", {**disponibilidad._AGENTES, "opencode": lambda s: 1 / 0})
    e = cap()["agentes"]["opencode"]
    assert e["estado"] == "SIN VERIFICAR" and e["causa"] == "comprobacion_fallida"


def test_sonda_real_de_openhands_distingue_ausente_de_fallo(vacio, monkeypatch):
    monkeypatch.setattr(disponibilidad._comun, "ejecutar_proceso", lambda *a, **k: {"exit_code": 3, "timeout": False})
    disponibilidad._CACHE.clear()
    assert disponibilidad._sonda_openhands(sys.executable) is False
    monkeypatch.setattr(disponibilidad._comun, "ejecutar_proceso", lambda *a, **k: {"exit_code": -9, "timeout": True})
    disponibilidad._CACHE.clear()
    assert disponibilidad._sonda_openhands(sys.executable) is None


def test_workflows_heredan_el_peor_bloqueo_definitivo(vacio, monkeypatch):
    w = cap()["workflows"]
    assert w["individual"]["estado"] == "DISPONIBLE" and w["individual"]["verificado"] is True
    assert w["swe_code"]["estado"] in ("NO INSTALADO", "NO CONFIGURADO") and w["swe_code"]["disponible"] is False
    assert w["liquid_mirror"]["estado"] == "NO CONFIGURADO"
    monkeypatch.setenv("SWECODE_URL_S2", "http://127.0.0.1:9102/v1"); monkeypatch.setenv("SWECODE_URL_S3", "http://127.0.0.1:9103/v1")
    monkeypatch.setenv("RIU_OPENHANDS_PYTHON", sys.executable)
    assert cap(sonda_openhands=lambda py: None)["workflows"]["liquid_mirror"]["estado"] == "SIN VERIFICAR"  # solo el verificador esta sin comprobar
    assert cap(sonda_openhands=lambda py: True)["workflows"]["liquid_mirror"]["estado"] == "DISPONIBLE"


def test_modelos_traen_nombre_y_proveedor_del_catalogo_unico(vacio):
    c = cap()["modelos"]
    assert set(c) == set(modelos.MODELOS)
    for mid, e in c.items():
        assert e["proveedor"] == modelos.MODELOS[mid]["provider"] and e["nombre"] == modelos.NOMBRES[mid]
    assert [x["id"] for x in modelos.catalogo()] == list(modelos.MODELOS)


def test_catalogo_unico_coincide_con_externos_y_sin_llama(vacio):
    from mvp import externos
    ext = {m: c["nombre"] for m, c in externos.PROVEEDORES_NUEVOS.items()}
    assert {m for m in modelos.MODELOS if not m.startswith("hf/")} == set(ext)  # 163: un solo catalogo; la lista del backend YAIWES no se contradice
    assert {m: modelos.NOMBRES[m] for m in ext} == ext
    assert not any("llama" in m for m in modelos.MODELOS)  # 148


def test_compatibilidad_agente_modelo(vacio, monkeypatch):
    ok, motivo = modelos.compatible("codex", "groq/qwen/qwen3.8-27b")
    assert ok is True and motivo == ""
    assert modelos.compatible("agente-inexistente", "groq/qwen/qwen3.8-27b")[0] is False
    assert modelos.compatible("codex", "modelo/inexistente")[0] is False
    ok, motivo = modelos.compatible("claude-code", "hf/qwen3-0.6b", permitidos=["nvidia/minimaxai/minimax-m3.1-flash"])
    assert ok is False and "nvidia/minimaxai/minimax-m3.1-flash" in motivo
    assert modelos.compatible("claude-code", "nvidia/minimaxai/minimax-m3.1-flash", permitidos=["nvidia/minimaxai/minimax-m3.1-flash"])[0] is True
    # matriz completa 6 x 9 sin excepciones
    for a in modelos.AGENTES:
        for m in modelos.MODELOS:
            assert isinstance(modelos.compatible(a, m)[0], bool)


def test_listas_del_frontend_y_del_bridge_no_contradicen_el_catalogo(vacio):
    """163/165/183: modelos.py es el catalogo unico. Las copias manuales que aun existan (frontend swe-directo.js, mini_router) no pueden traer ids que el catalogo no tenga ni Llama."""
    import pathlib
    import re
    raiz = pathlib.Path(__file__).resolve().parents[3]
    ids_ext = {m for m in modelos.MODELOS if not m.startswith("hf/")}
    front = (raiz / "chat/frontend/swe-directo.js").read_text(encoding="utf-8")
    vistos = set(re.findall(r'"((?:groq|nvidia)/[A-Za-z0-9._/-]+)"', front))
    assert vistos <= ids_ext, vistos - ids_ext
    assert not re.search(r'"(?:groq|nvidia)/[^"]*llama', front, re.I)
    import importlib.util
    spec = importlib.util.spec_from_file_location("mini_router_a5", raiz / "SWE CODE/mini_router.py")
    mr = importlib.util.module_from_spec(spec); spec.loader.exec_module(mr)
    del_mini = {"groq/" + m for m in [mr.MODELOS_DEFECTO["groq"]] + mr.MODELOS_RESPALDO["groq"]} | {"nvidia/" + m for m in [mr.MODELOS_DEFECTO["nvidia"]] + mr.MODELOS_RESPALDO["nvidia"]}
    assert del_mini == ids_ext  # el respaldo del mini-router usa exactamente los modelos autorizados
