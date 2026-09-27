"""Tests SIMULADO de la Puerta de Evidencia T07. Cero red."""
import os
import sys

os.environ["SIMULADO"] = "1"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import parser as parser_mod          # noqa: E402
import goals                          # noqa: E402
import compilador_busquedas           # noqa: E402
import buscadores                     # noqa: E402
import extractor                      # noqa: E402
import ranking                        # noqa: E402
import evidence_pack as pack_mod      # noqa: E402
import verificador                    # noqa: E402
import puerta                         # noqa: E402


def test_parser_task_types():
    assert parser_mod.parse("instala pytest con pip")["task_type"] == "INSTALL"
    assert parser_mod.parse("despliega la app a produccion")["task_type"] == "DEPLOY"
    assert parser_mod.parse("arregla el traceback del test")["task_type"] == "DEBUG"
    assert parser_mod.parse("compara CRAG vs RARR")["task_type"] == "COMPARE"
    p = parser_mod.parse("busca la version de requests en github.com/psf/requests")
    assert p["task_type"] == "SEARCH"
    assert any("requests" in t for t in p["targets"])


def test_goals_12_presentes():
    assert goals.GOAL_IDS == ["G%02d" % i for i in range(1, 13)]
    for gid in goals.GOAL_IDS:
        g = goals.get_goal(gid)
        assert g["entrada"] and g["salida"] and g["plantillas"]


def test_compilador_determinista():
    parsed = parser_mod.parse("despliega proyecto v2.3.1")
    q1 = compilador_busquedas.compilar(parsed)
    q2 = compilador_busquedas.compilar(parsed)
    assert q1 == q2
    assert len(q1) >= 12
    assert any("latest release" in q["query"] for q in q1)


def test_buscadores_simulado_sin_red():
    assert buscadores.SIMULADO is True
    res = buscadores.fanout([{"goal": "G06", "query": "proyecto latest release"}])
    assert res
    for r in res:
        for campo in ("query", "source", "url", "title", "date",
                      "snippet", "source_type", "retrieved_at"):
            assert campo in r


def test_extractor_fragmentos():
    texto = "# Titulo\n\nParrafo con version 2.3.1 vigente.\n\n```\npytest -q\n```"
    hall = extractor.extraer(texto, ["version", "pytest"])
    assert hall
    assert any(h["tipo"] == "code" for h in hall)


def test_ranking_bm25_y_rrf_deterministas():
    docs = ["pytest tests guia oficial", "blog antiguo version 1.0",
            "release v2.3.1 changelog tests pass"]
    s1 = ranking.bm25_scores(docs, "pytest tests")
    s2 = ranking.bm25_scores(docs, "pytest tests")
    assert s1 == s2
    assert s1[0] == max(s1)
    r1 = [{"url": "a", "title": "a"}, {"url": "b", "title": "b"}]
    r2 = [{"url": "b", "title": "b"}, {"url": "c", "title": "c"}]
    fusion = ranking.rrf([r1, r2])
    assert fusion[0][1]["url"] == "b"  # b aparece en ambos rankings
    assert fusion == ranking.rrf([r1, r2])


def test_evidence_pack_campos():
    parsed = parser_mod.parse("busca documentacion de pytest")
    res = buscadores.fanout([{"goal": "G05", "query": "pytest documentacion"}])
    rankeados = ranking.rankear(res, "pytest documentacion")
    pack = pack_mod.construir("busca documentacion de pytest", parsed, rankeados)
    for campo in ("task", "known_facts", "requirements", "constraints",
                  "conflicts", "unknown", "sources"):
        assert campo in pack
    assert pack["known_facts"]


def test_puerta_pass_completo():
    pack = puerta.antes("busca la documentacion oficial del proyecto version 2.3.1")
    resultado = {"claims": [
        {"tipo": "http", "url": "https://docs.ejemplo.dev/proyecto"},
        {"tipo": "version", "obtenida": "2.3.1", "esperada": "2.3.1"},
        {"tipo": "tests", "comando": "pytest -q"},
    ]}
    r = puerta.despues("busca la documentacion oficial del proyecto version 2.3.1",
                       resultado, pack=pack)
    assert r["veredicto"] == "PASS"
    assert set(r["detalle_goals"].keys()) == set(goals.GOAL_IDS)
    assert all(d["ok"] for d in r["detalle_goals"].values())


def test_puerta_incomplete_sin_evidencia(monkeypatch):
    monkeypatch.setattr(buscadores, "fanout", lambda qs, raiz=".": [])
    pack = puerta.antes("investiga algo sin fuentes")
    r = puerta.despues("investiga algo sin fuentes", {"claims": []}, pack=pack)
    assert r["veredicto"] == "INCOMPLETE"
    assert not r["detalle_goals"]["G12"]["ok"]


def test_puerta_contradiction():
    facts = [
        {"fact": "La version 1.0 es la recomendada", "source": "blog", "score": 1.0},
        {"fact": "Latest release v2.3.1 version vigente", "source": "github", "score": 2.0},
    ]
    conflicts = pack_mod.detectar_conflictos(facts)
    assert conflicts
    pack = {"known_facts": facts, "conflicts": conflicts, "unknown": [],
            "sources": [], "parsed": parser_mod.parse("verifica version")}
    r = puerta.despues("verifica version", {"claims": []}, pack=pack)
    assert r["veredicto"] == "CONTRADICTION"
    assert not r["detalle_goals"]["G11"]["ok"]


def test_puerta_fail_restriccion_violada():
    pack = puerta.antes("modifica el codigo, prohibido tocar secretos")
    pack["parsed"]["forbidden"] = ["tocar secretos"]
    r = puerta.despues("modifica el codigo, prohibido tocar secretos",
                       "se decidio tocar secretos del repo", pack=pack)
    assert r["veredicto"] == "FAIL"
    assert not r["detalle_goals"]["G03"]["ok"]


def test_puerta_fail_ejecucion():
    pack = puerta.antes("verifica que el archivo existe")
    resultado = {"claims": [{"tipo": "archivo", "ruta": "/no/existe/este-archivo.txt"}]}
    r = puerta.despues("verifica que el archivo existe", resultado, pack=pack)
    assert r["veredicto"] == "FAIL"


def test_verificador_no_confia_en_ejecutor():
    # El ejecutor afirma que el archivo existe; el verificador comprueba de verdad.
    check = verificador.verificar_archivo("/ruta/inventada/por/el/ejecutor.py")
    assert check["ok"] is False
    check_http = verificador.verificar_http("https://docs.ejemplo.dev/proyecto")
    assert check_http["ok"] is True  # SIMULADO: valida forma, sin red
