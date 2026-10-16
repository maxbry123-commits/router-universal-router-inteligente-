"""Fix B: reintentos 'deja de razonar', sentinela y anexos en preguntas simples (mocks, sin red)."""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1] / "router inteligente universal"
sys.path.insert(0, str(ROOT))
from plugins.puente_chat import plugin as pc  # noqa: E402
from plugins.puente_chat.fichas import sentinela as sen  # noqa: E402
from plugins.fichas_qwen import plugin as fq  # noqa: E402


def _resp(content="", reasoning=None):
    m = {"role": "assistant", "content": content}
    if reasoning:
        m["reasoning_content"] = reasoning
    return {"choices": [{"message": m}]}


@pytest.fixture
def fast():
    t = pc._PERFIL.set("fast")
    yield
    pc._PERFIL.reset(t)


def test_vacio_con_reasoning_max_1_reintento_y_devuelve_texto(fast):
    llamadas = []
    def llamar(ms, tools):
        llamadas.append(1)
        return 200, _resp("", "razonamiento largo... la respuesta es 42")
    d, _ = pc._bucle(llamar, [{"role": "user", "content": "hola"}])
    assert len(llamadas) <= 2  # 1 llamada + como mucho 1 reintento
    assert "42" in d["choices"][0]["message"]["content"]
    assert sen._valido(d)  # el sentinela ya no lo relanza


@pytest.fixture
def normal():
    t = pc._PERFIL.set("normal")
    yield
    pc._PERFIL.reset(t)


def test_fast_sin_reintento_razonar(fast):
    n = []
    d, _ = pc._bucle(lambda ms, t: (n.append(1), (200, _resp("", "pensando 42")))[1], [{"role": "user", "content": "x"}])
    assert len(n) == 1 and "42" in d["choices"][0]["message"]["content"]


def test_reintento_que_responde_bien(normal):
    seq = [_resp("", "pensando"), _resp("Hola, soy Qwen")]
    d, _ = pc._bucle(lambda ms, t: (200, seq.pop(0)), [{"role": "user", "content": "x"}])
    assert d["choices"][0]["message"]["content"] == "Hola, soy Qwen"


def test_timeout_no_da_5_vueltas():
    n = []
    def paso(ms):
        n.append(1)
        return {"error": "PROVEEDOR_TIMEOUT_O_RED"}, []
    cl = sen.ejecutar([("modelo", paso)], [])
    assert len(n) == 1 and cl["estado"] == "GAP_FINAL"


def test_timeout_pasa_a_reserva_sin_relanzar():
    n = {"a": 0, "b": 0}
    def a(ms):
        n["a"] += 1; return {"error": "PROVEEDOR_TIMEOUT_O_RED"}, []
    def b(ms):
        n["b"] += 1; return _resp("ok"), []
    cl = sen.ejecutar([("modelo", a), ("reserva:x", b)], [])
    assert cl["completada"] and n == {"a": 1, "b": 1}


def test_vacio_cierra_con_lo_que_haya():
    n = []
    def paso(ms):
        n.append(1); return _resp("", "solo razonamiento"), []
    cl = sen.ejecutar([("modelo", paso)], [])
    assert len(n) == 1
    assert cl["resultado"][0]["choices"][0]["message"]["reasoning_content"] == "solo razonamiento"


def test_error_transitorio_max_2_vueltas():
    n = []
    cl = sen.ejecutar([("modelo", lambda ms: (n.append(1), ({"error": "MODELO_NO_RESPONDE"}, []))[1])], [])
    assert sen.MAX_VUELTAS == 2 and len(n) == 2 and not cl["completada"]


OPTS_GOB = {"gobernanza": {"anexo_memoria": {"enabled": True, "fases": ["entrada", "salida"]}}}


def _spy(monkeypatch):
    llam = []
    monkeypatch.setattr(fq, "_llamar_harness_1", lambda *a, **k: llam.append(a) or "ENTRADA_OK")
    return llam


def test_simple_cero_anexos(monkeypatch):
    llam = _spy(monkeypatch)
    o = {**OPTS_GOB}
    assert fq._anexo({}, "entrada", "qué modelo eres", o) == ""
    o["es_simple"] = fq._es_simple("qué modelo eres", o, {"N4": {}})
    assert fq._anexo({}, "salida", "Soy Qwen", o) == ""
    assert llam == []


def test_compleja_anexos_siguen(monkeypatch):
    llam = _spy(monkeypatch)
    msg = "modifica el archivo main.py y agrega un endpoint nuevo"
    o = {**OPTS_GOB, "es_simple": fq._es_simple(msg, OPTS_GOB, {"N4": {}})}
    assert o["es_simple"] is False
    assert fq._anexo({}, "entrada", msg, o) == "ENTRADA_OK"
    assert fq._anexo({}, "salida", "hecho", o) == "ENTRADA_OK"
    assert len(llam) == 2
