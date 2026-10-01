"""Tests SIMULADO de la Puerta de Evidencia T07. Cero red."""
import hashlib
import json
import os
import sys

import pytest

os.environ["SIMULADO"] = "1"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import buscadores
import compilador_busquedas
import evidence_pack as pack_mod
import extractor
import goals
import parser as parser_mod
import puerta
import ranking
import verificador


def test_parser_task_types():
    assert parser_mod.parse("instala pytest con pip")["task_type"] == "INSTALL"
    assert parser_mod.parse("despliega la app a produccion")["task_type"] == "DEPLOY"
    assert parser_mod.parse("arregla el traceback del test")["task_type"] == "DEBUG"
    assert parser_mod.parse("compara CRAG vs RARR")["task_type"] == "COMPARE"
    p = parser_mod.parse("busca la version de requests en github.com/psf/requests")
    assert p["task_type"] == "SEARCH"
    assert any("requests" in t for t in p["targets"])


@pytest.mark.parametrize(("instruction", "expected"), [
    ("busca documentación", "SEARCH"),
    ("instala pytest", "INSTALL"),
    ("descarga archivo", "DOWNLOAD"),
    ("extrae paquete", "EXTRACT"),
    ("despliega aplicación", "DEPLOY"),
    ("modifica código", "MODIFY_CODE"),
    ("depura error", "DEBUG"),
    ("prueba el backend", "TEST"),
    ("compara versiones", "COMPARE"),
    ("audita el router", "AUDIT"),
    ("investiga componentes", "RESEARCH"),
    ("verifica el hash", "VERIFY"),
])
def test_parser_t11_known_inputs_are_deterministic(instruction, expected):
    assert parser_mod.parse(instruction) == parser_mod.parse(instruction)
    assert parser_mod.parse(instruction)["task_type"] == expected


def test_parser_t11_unknown_and_negated_instruction_fail_closed():
    assert parser_mod.parse("no deploy")["task_type"] == "UNKNOWN"
    assert parser_mod.parse("no deploy")["forbidden"] == ["deploy"]
    assert parser_mod.parse("quizá más adelante")["task_type"] == "UNKNOWN"
    assert parser_mod.parse(None)["task_type"] == "UNKNOWN"
    assert compilador_busquedas.compilar(parser_mod.parse("no deploy")) == []
    assert parser_mod.parse("modifica código; no deploy")["task_type"] == "MODIFY_CODE"

    pack = {
        "parsed": parser_mod.parse("no deploy"),
        "known_facts": [{"fact": "existe archivo"}],
        "conflicts": [],
        "unknown": [],
        "sources": ["local"],
    }
    result = puerta.despues("no deploy", {"claims": []}, pack=pack)
    assert result["veredicto"] == "INCOMPLETE"
    assert not result["detalle_goals"]["G01"]["ok"]


def test_goals_12_presentes():
    assert goals.GOAL_IDS == [f"G{i:02}" for i in range(1, 13)]
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
    assert all(q["id"] and q["text"] == q["query"] and q["required"] for q in q1)
    assert all(q["source_scope"] == ["github", "local"] for q in q1)
    assert len({" ".join(q["text"].split()).casefold() for q in q1}) == len(q1)


def test_buscadores_simulado_sin_red():
    assert buscadores.simulado() is True
    res = buscadores.fanout([{"goal": "G06", "query": "proyecto latest release"}])
    assert res
    for r in res:
        for campo in ("query", "source", "url", "title", "date",
                      "snippet", "source_type", "retrieved_at"):
            assert campo in r


def test_fanout_falla_cerrado_por_motor_sin_perder_evidencia_local(monkeypatch):
    def github_unavailable(query, *, strict=False):
        raise OSError("github unavailable")

    monkeypatch.setenv("SIMULADO", "0")
    monkeypatch.setattr(buscadores, "buscar_github", github_unavailable)
    monkeypatch.setattr(buscadores, "buscar_local", lambda query, raiz: [{
        "query": query, "source": "local", "url": "repo://README.md",
        "title": "README", "date": "", "snippet": "documentacion local",
        "source_type": "local", "retrieved_at": "2026-10-01T00:00:00Z",
    }])
    observed = buscadores.fanout_observado([
        {"id": "q1", "query": "documentacion", "source_scope": ["github", "local", "unknown"]},
    ])
    assert len(observed["results"]) == 1
    assert observed["results"][0]["query_id"] == "q1"
    assert observed["observations"] == [
        {"query_id": "q1", "source": "github", "code": "OSError"},
        {"query_id": "q1", "source": "unknown", "code": "UNAUTHORIZED_ADAPTER"},
    ]
    pack = puerta.antes("busca documentacion")
    assert pack["known_facts"] and pack["observations"]
    assert puerta.despues("busca documentacion", {"claims": []}, pack=pack)["veredicto"] == "INCOMPLETE"


def test_busqueda_local_expone_timeout_sin_resultados_parciales(tmp_path, monkeypatch):
    (tmp_path / "README.md").write_text("documentacion", encoding="utf-8")
    clock = iter((0, 11))
    monkeypatch.setattr(buscadores.time, "monotonic", lambda: next(clock, 11))
    with pytest.raises(TimeoutError):
        buscadores.buscar_local("documentacion", str(tmp_path))


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
    assert all(fact["source"] for fact in pack["known_facts"])
    assert pack["packet_hash"] == hashlib.sha256(
        json.dumps(
            {key: value for key, value in pack.items() if key != "packet_hash"},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


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
    pack["known_facts"][0]["fact"] = "afirmacion alterada tras la busqueda"
    assert puerta.despues(
        "busca la documentacion oficial del proyecto version 2.3.1", resultado, pack=pack,
    )["veredicto"] == "INCOMPLETE"


def test_puerta_verifica_parser_consultas_observaciones_y_fuentes():
    entrada = "busca la documentacion oficial del proyecto version 2.3.1"
    resultado = {"claims": [
        {"tipo": "http", "url": "https://docs.ejemplo.dev/proyecto"},
        {"tipo": "version", "obtenida": "2.3.1", "esperada": "2.3.1"},
        {"tipo": "tests", "comando": "pytest -q"},
    ]}
    original = puerta.antes(entrada)
    assert puerta.despues(entrada, resultado, pack=original)["veredicto"] == "PASS"
    for key, replacement in (
        ("parsed", {"task_type": "UNKNOWN"}),
        ("queries", []),
        ("observations", [{"source": "github", "code": "OSError"}]),
    ):
        changed = json.loads(json.dumps(original))
        changed[key] = replacement
        assert puerta.despues(entrada, resultado, pack=changed)["veredicto"] == "INCOMPLETE"
    changed = json.loads(json.dumps(original))
    changed["sources"] = []
    changed["packet_hash"] = pack_mod.packet_hash(changed)
    assert puerta.despues(entrada, resultado, pack=changed)["veredicto"] == "INCOMPLETE"


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


def test_claims_falsos_y_no_verificables_fallan_cerrado(tmp_path):
    file = tmp_path / "prueba.txt"
    file.write_text("contenido original", encoding="utf-8")
    good_hash = hashlib.sha256(file.read_bytes()).hexdigest()
    pack = {
        "parsed": parser_mod.parse("verifica el archivo"), "known_facts": [{"fact": "archivo"}],
        "conflicts": [], "unknown": [], "sources": ["local"],
    }
    for claim in (
        {"tipo": "hash", "ruta": str(file), "sha256": "0" * 64},
        {"tipo": "otro", "ruta": str(file)},
        {"tipo": "archivo", "ruta": str(tmp_path)},
        {"tipo": "http", "url": None},
        {"tipo": "tests", "comando": ""},
        None,
    ):
        result = puerta.despues("verifica el archivo", {"claims": [claim]}, pack=pack)
        assert result["veredicto"] == "FAIL"
        assert any(not check["ok"] for check in result["checks"])
    assert puerta.despues("verifica el archivo", {"claims": "invalido"}, pack=pack)["veredicto"] == "FAIL"
    assert verificador.verificar_hash(str(file), good_hash)["ok"]
    file.write_text("contenido alterado", encoding="utf-8")
    assert not verificador.verificar_hash(str(file), good_hash)["ok"]
