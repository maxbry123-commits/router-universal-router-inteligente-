import asyncio
import web_search_tool
import gap_resolution_loop as glp


def test_default_engine_usa_buscar_web(monkeypatch):
    async def fake_search(q, max_results=8):
        return [{"title": "fastapi docs", "url": "https://fastapi.tiangolo.com/x", "snippet": "fastapi routing"}]

    async def fake_fetch(url):
        return "fastapi routing guide"

    monkeypatch.setattr(web_search_tool, "search", fake_search)
    monkeypatch.setattr(web_search_tool, "fetch_text", fake_fetch)
    eng = glp.default_engine()
    res = asyncio.run(eng.run("fastapi routing", set()))
    assert res["status"] == "OK"
    assert res["sources"] == ["https://fastapi.tiangolo.com/x"]


def test_gap_loop_resuelve_con_evidencia(monkeypatch):
    async def fake_search(q, max_results=8):
        return [{"title": "fastapi docs", "url": "https://fastapi.tiangolo.com/x", "snippet": "fastapi routing"}]

    async def fake_fetch(url):
        return "fastapi routing guide"

    monkeypatch.setattr(web_search_tool, "search", fake_search)
    monkeypatch.setattr(web_search_tool, "fetch_text", fake_fetch)
    outs = iter(["GAP: fastapi routing", "respuesta final"])

    async def model(prompt):
        return next(outs)

    loop = glp.GapResolutionLoop(glp.default_engine(), max_rounds=3)
    assert asyncio.run(loop.run(model, "pregunta")) == "respuesta final"
