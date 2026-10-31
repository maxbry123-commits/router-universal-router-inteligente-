"""Dispatcher: solo adaptadores autorizados; exige dict, ok True y recibo."""
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
