"""Dispatcher: solo adaptadores autorizados; exige dict, ok True y recibo."""
import re
import sys
import types
import pytest

from agentes.adaptadores import dispatcher


def instalar(monkeypatch, modulo, resultado=None, exc=None):
    m = types.ModuleType("agentes.adaptadores." + modulo)
    llamadas = []
    def run(tarea_id, modelo, objetivo, contexto, permisos, checkpoint):
        llamadas.append((tarea_id, modelo, objetivo, contexto, permisos, checkpoint))
        if exc:
            raise exc
        return resultado
    m.run = run
    monkeypatch.setitem(sys.modules, "agentes.adaptadores." + modulo, m)
    return llamadas


ARGS = dict(tarea_id="t-1", modelo="hf/lfm2.5-350m", objetivo="x", contexto="", permisos={}, checkpoint={})


def test_mapa_de_adaptadores_exacto():
    assert dispatcher.ADAPTADORES == {"codex": "codex", "opencode": "opencode", "swe-agent": "swe_agent", "openhands": "openhands",
                                      "claude-code": "claude_code", "openclaw": "openclaw"}


def test_agente_no_autorizado():
    with pytest.raises(ValueError, match="AGENTE_NO_AUTORIZADO"):
        dispatcher.ejecutar_agente("bash", **ARGS)


def test_camino_feliz_llama_al_adaptador(monkeypatch):
    r = {"ok": True, "agente": "swe-agent", "task_id": "t-1", "resultado": "r", "herramientas": [], "evidencias": [], "recibo": "swe-agent:t-1:abc", "exit_code": 0}
    ll = instalar(monkeypatch, "swe_agent", r)
    assert dispatcher.ejecutar_agente("swe-agent", **ARGS) == r
    assert ll == [("t-1", "hf/lfm2.5-350m", "x", "", {}, {})]


@pytest.mark.parametrize("res,codigo", [("texto", "RESULTADO_AGENTE_INVALIDO"), (None, "RESULTADO_AGENTE_INVALIDO"),
                                        ({"ok": False, "codigo": "AGENTE_NO_INSTALADO", "error": "x"}, "EJECUCION_AGENTE_FALLIDA"),
                                        ({"ok": "true", "recibo": "r"}, "EJECUCION_AGENTE_FALLIDA"),
                                        ({"ok": True}, "AGENTE_SIN_RECIBO"), ({"ok": True, "recibo": ""}, "AGENTE_SIN_RECIBO"),
                                        ({"ok": True, "recibo": None}, "AGENTE_SIN_RECIBO")])
def test_validaciones_del_resultado(monkeypatch, res, codigo):
    instalar(monkeypatch, "codex", res)
    with pytest.raises(ValueError, match=codigo) as e:
        dispatcher.ejecutar_agente("codex", **ARGS)
    assert getattr(e.value, "resultado", res) == res or res is None or isinstance(res, str)


def test_el_error_conserva_el_resultado_del_adaptador(monkeypatch):
    res = {"ok": False, "codigo": "AGENTE_NO_INSTALADO", "error": "falta", "efectos_posibles": False}
    instalar(monkeypatch, "codex", res)
    with pytest.raises(dispatcher.AgenteError) as e:
        dispatcher.ejecutar_agente("codex", **ARGS)
    assert e.value.resultado == res and e.value.codigo == "EJECUCION_AGENTE_FALLIDA" and isinstance(e.value, ValueError)


def test_excepcion_del_adaptador_se_trata_como_fallo_con_efectos_posibles(monkeypatch):
    instalar(monkeypatch, "codex", exc=RuntimeError("boom"))
    with pytest.raises(dispatcher.AgenteError) as e:
        dispatcher.ejecutar_agente("codex", **ARGS)
    assert e.value.resultado["efectos_posibles"] is True and e.value.resultado["codigo"] == "ADAPTADOR_EXCEPCION"


# ---------------- A2 73-76: los adaptadores viven solo en agentes/adaptadores y el dispatcher es el unico punto de seleccion ----------------
def test_adaptadores_solo_en_agentes_adaptadores_y_sin_copias_en_yaiwes_ni_swe_code():
    import os
    raiz = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # chat-router
    from agentes.adaptadores.dispatcher import ADAPTADORES
    esperados = {m + ".py" for m in ADAPTADORES.values()}
    for ambito in ("chat/backend", "SWE CODE", "SWE CODE free", "chat/frontend"):
        for dirpath, dirs, files in os.walk(os.path.join(raiz, ambito)):
            dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".git")]
            copias = esperados & set(files)
            assert not copias, "implementacion duplicada de adaptador en %s: %s" % (dirpath, copias)


def test_el_harness_y_los_workflows_eligen_adaptador_solo_por_el_dispatcher():
    import inspect
    import os
    from agentes.adaptadores import workflows
    assert "import_module" not in inspect.getsource(workflows) and not re.search(r"from \. import .*\b(codex|opencode|openhands|swe_agent|claude_code)\b", inspect.getsource(workflows))
    ctx = workflows.Contexto(guardar=None, leer=None, llm=None, router=None, con_efectos=None, diario=None, anotar=None, llave=None, secreto=None)
    assert ctx.ejecutar_agente is dispatcher.ejecutar_agente
    harness = os.path.join(os.path.dirname(__file__), "..", "..", "..", "chat", "backend", "deepseek_harness", "server.py")
    fuente = open(harness, encoding="utf-8").read()
    assert "from agentes.adaptadores.dispatcher import ejecutar_agente" in fuente and not re.search(r"adaptadores\.(codex|opencode|openhands|swe_agent|claude_code|openclaw)\b", fuente)


@pytest.mark.parametrize("cambio,codigo", [
    ({"agente": "openhands"}, "IDENTIDAD_RECIBO_INCORRECTA"),
    ({"task_id": "otra-tarea"}, "IDENTIDAD_RECIBO_INCORRECTA"),
    ({"recibo": "openhands:t-1:abc"}, "RECIBO_NO_CORRESPONDE"),
    ({"recibo": "codex:otra-tarea:abc"}, "RECIBO_NO_CORRESPONDE"),
    ({"exit_code": 1}, "EXIT_CODE_NO_CONFIRMADO"),
    ({"exit_code": True}, "EXIT_CODE_NO_CONFIRMADO"),
    ({"exit_code": None}, "EXIT_CODE_NO_CONFIRMADO"),
    ({"truncado": True}, "SALIDA_AGENTE_TRUNCADA"),
    ({"resultado": ""}, "RESULTADO_AGENTE_VACIO"),
    ({"herramientas": "read"}, "EVIDENCIA_AGENTE_INVALIDA"),
    ({"evidencias": None}, "EVIDENCIA_AGENTE_INVALIDA"),
])
def test_xray_no_acepta_recibo_incorrecto(monkeypatch, cambio, codigo):
    valido = {"ok": True, "agente": "codex", "task_id": "t-1", "resultado": "hecho", "herramientas": [], "evidencias": [],
              "recibo": "codex:t-1:abc", "exit_code": 0}
    instalar(monkeypatch, "codex", {**valido, **cambio})
    with pytest.raises(dispatcher.AgenteError) as e:
        dispatcher.ejecutar_agente("codex", **ARGS)
    assert e.value.codigo == codigo


def test_xray_recibo_correcto(monkeypatch):
    valido = {"ok": True, "agente": "codex", "task_id": "t-1", "resultado": "hecho", "herramientas": ["read"],
              "evidencias": ["prueba:test"], "recibo": "codex:t-1:abc", "exit_code": 0, "truncado": False}
    instalar(monkeypatch, "codex", valido)
    assert dispatcher.ejecutar_agente("codex", **ARGS) == valido
