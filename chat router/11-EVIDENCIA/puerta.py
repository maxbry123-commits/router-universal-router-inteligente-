"""Puerta de Evidencia T07 (Evidence/Search Gate).

antes(input)  -> evidence_pack (investigacion previa al ejecutor)
despues(input, resultado) -> PASS | INCOMPLETE | CONTRADICTION | FAIL
con detalle por goal (G01..G12).

Regla del Director: la IA que ejecuto no cierra su propio trabajo;
el cierre se decide con evidencia y comprobaciones independientes.
"""
import json
import os
import sys

import buscadores
import compilador_busquedas
import evidence_pack as pack_mod
import extractor
import goals as goals_mod
import parser as parser_mod
import ranking
import verificador

SIMULADO = os.environ.get("SIMULADO", "") == "1"

PASS = "PASS"
INCOMPLETE = "INCOMPLETE"
CONTRADICTION = "CONTRADICTION"
FAIL = "FAIL"

# Goals que exigen comprobacion posterior real (no basta evidencia documental).
_GOALS_EJECUCION = {"G09", "G10"}


def antes(entrada, raiz="."):
    """Fase previa: parsea, compila consultas, busca, extrae, rankea y empaqueta."""
    parsed = parser_mod.parse(entrada)
    consultas = compilador_busquedas.compilar(parsed)
    busqueda = buscadores.fanout_observado(consultas, raiz=raiz)
    resultados = busqueda["results"]
    terminos = parsed["targets"] or [parsed["raw"][:40]]
    hallazgos = extractor.extraer_de_resultados(resultados, terminos)
    rankeados = ranking.rankear(resultados, entrada)
    pack = pack_mod.construir(entrada, parsed, rankeados, hallazgos)
    pack["parsed"] = parsed
    pack["queries"] = consultas
    pack["observations"] = busqueda["observations"]
    if busqueda["observations"]:
        pack["unknown"].append("errores de motores de busqueda; evidencia incompleta")
        pack["packet_hash"] = pack_mod.packet_hash(pack)
    return pack


def _detalle_goals(pack, checks):
    """Evalua cada goal G01..G12 con evidencia y comprobaciones."""
    detalle = {}
    hay_evidencia = bool(pack.get("known_facts"))
    checks_ok = {c["check"]: c["ok"] for c in checks}
    task_type = pack.get("parsed", {}).get("task_type", "UNKNOWN")
    requires_tests = task_type in {
        "MODIFY_CODE", "DEBUG", "TEST", "INSTALL", "DOWNLOAD", "EXTRACT", "DEPLOY",
    }
    for gid in goals_mod.GOAL_IDS:
        ok = hay_evidencia
        nota = "evidencia documental" if hay_evidencia else "sin evidencia"
        if gid == "G03":
            ok = checks_ok.get("restricciones", True)
            nota = "restricciones respetadas" if ok else "restriccion violada"
        elif gid == "G01" and task_type == "UNKNOWN":
            ok = False
            nota = "intencion no reconocida"
        elif gid == "G06":
            if "version" in checks_ok:
                ok = checks_ok["version"]
                nota = "version verificada" if ok else "version incorrecta"
        elif gid == "G09":
            ok = (
                checks_ok.get("tests") is True if requires_tests
                else any(c["ok"] for c in checks if c["check"] in ("archivo", "hash", "http", "version", "tests"))
            )
            nota = "ejecucion comprobada" if ok else "ejecucion no demostrada"
        elif gid == "G10":
            if requires_tests:
                ok = checks_ok.get("tests") is True
                nota = "tests pasan" if ok else "tests requeridos no demostrados"
            elif "tests" in checks_ok:
                ok = checks_ok["tests"]
                nota = "tests pasan" if ok else "tests fallan"
        elif gid == "G11":
            ok = not pack.get("conflicts")
            nota = "sin contradicciones" if ok else "contradicciones detectadas"
        elif gid == "G12":
            ok = hay_evidencia and not pack.get("unknown")
            nota = "evidencia suficiente" if ok else "evidencia insuficiente"
        detalle[gid] = {"ok": bool(ok), "nota": nota,
                        "goal": goals_mod.get_goal(gid)["nombre"]}
    return detalle


def despues(entrada, resultado, pack=None, claims=None, raiz="."):
    """Fase posterior: verifica claims de forma independiente y emite veredicto.

    resultado: dict con al menos {"claims": [...]} o texto libre.
    """
    if pack is None:
        pack = antes(entrada, raiz=raiz)
    if isinstance(resultado, dict):
        claims = claims if claims is not None else resultado.get("claims", [])
        texto_resultado = str(resultado)
    else:
        claims = claims or []
        texto_resultado = str(resultado)

    checks = verificador.verificar_claims(claims)
    checks.append(verificador.verificar_restricciones(
        texto_resultado, pack.get("parsed", {}).get("forbidden", [])))

    detalle = _detalle_goals(pack, checks)

    # Veredicto.
    if pack.get("conflicts"):
        veredicto = CONTRADICTION
    elif any(not c["ok"] for c in checks):
        veredicto = FAIL
    elif not pack_mod.verificar_packet(pack) or not pack.get("known_facts") or pack.get("unknown"):
        veredicto = INCOMPLETE
    elif all(d["ok"] for d in detalle.values()):
        veredicto = PASS
    else:
        veredicto = INCOMPLETE

    return {
        "veredicto": veredicto,
        "detalle_goals": detalle,
        "checks": checks,
        "conflicts": pack.get("conflicts", []),
        "fuentes": len(pack.get("sources", [])),
    }


if __name__ == "__main__":
    entrada = " ".join(sys.argv[1:]) or "buscar documentacion de pytest"
    p = antes(entrada)
    r = despues(entrada, {"claims": []}, pack=p)
    print(json.dumps(r, ensure_ascii=False, indent=2))
