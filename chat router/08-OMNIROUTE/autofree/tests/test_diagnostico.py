"""T10: pruebas deterministas; cero llamadas externas."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).parents[1] / "diagnostico.py"
spec = importlib.util.spec_from_file_location("yaiwes_autofree_diagnostico", MODULE)
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


def test_local_base_rechaza_destino_remoto_y_userinfo():
    for url in ("https://127.0.0.1:20128", "http://example.com",
                "http://user:pass@127.0.0.1:20128",
                "http://127.0.0.1:20128/private",
                "http://127.0.0.1:20128?token=abc"):
        try:
            diag.local_base(url)
        except ValueError:
            pass
        else:
            raise AssertionError(f"permitió destino no aceptado: {url}")
    assert diag.local_base("http://127.0.0.1:20128/") == "http://127.0.0.1:20128"


def test_clasificador_distingue_http_exitoso_vacio_y_fallos():
    ok = {"choices": [{"message": {"content": "OMNI_OK"}}]}
    empty = {"choices": [{"message": {"content": ""}}]}
    assert diag.classify(200, ok) == "PASS"
    assert diag.classify(200, empty) == "EMPTY_RESPONSE"
    assert diag.classify(200, {"error": "bad"}) == "EMPTY_RESPONSE"
    for http in (401, 403):
        assert diag.classify(http, {}) == "ACCESS_DENIED"
    for http in (418, 429):
        assert diag.classify(http, {}) == "RATE_OR_ANTIABUSE_LIMIT"
    for http in (400, 404, 406, 422):
        assert diag.classify(http, {}) == "INVALID_MODEL_OR_REQUEST"
    assert diag.classify(502, {}) == "UPSTREAM_OR_GATEWAY_ERROR"
    assert diag.classify(0, {}) == "CONNECTION_ERROR"


def test_contenido_structurado_y_catalogo():
    assert diag.has_assistant_text({
        "choices": [{"message": {"content": [{"type": "text", "text": "hola"}]}}]
    })
    assert not diag.has_assistant_text({"choices": []})
    assert diag.models_from_response({"data": [{"id": "x/y"}, {"bad": 1}, "ignored"]}) == {"x/y"}


def test_probe_una_vez_sin_repetir_y_no_gasta_conocidos_fallidos():
    ok = {"choices": [{"message": {"content": "OMNI_OK"}}]}
    def fake(base, route, timeout=12, payload=None):
        if route == "/api/monitoring/health":
            return 200, {"status": "ok"}
        if route == "/v1/models":
            return 200, {"data": [{"id": "oc/big-pickle"}, {"id": "test/free"}]}
        if route == "/v1/chat/completions":
            assert payload["model"] == "test/free"
            return 200, ok
        raise AssertionError(route)
    with patch.object(diag, "fetch_json", side_effect=fake) as mocked:
        result = diag.audit("http://127.0.0.1:20128",
                            ["oc/big-pickle", "test/free", "other/no-model"])
    assert result["probe_count"] == 1
    assert [x["classification"] for x in result["results"]] == [
        "SKIPPED_PREVIOUS_ACCESS_ERROR", "PASS", "NOT_IN_CATALOG"]
    assert mocked.call_count == 3


def test_no_hace_chat_si_health_no_responde():
    with patch.object(diag, "fetch_json",
                      side_effect=[(503, {}), (200, {"data": [{"id": "test/free"}]})]) as mocked:
        result = diag.audit("http://127.0.0.1:20128", ["test/free"])
    assert mocked.call_count == 2
    assert result["probe_count"] == 0


def test_limite_maximo_modelos_ante_cli():
    import pytest
    with pytest.raises(SystemExit):
        diag.main(["--modelo", "m1", "--modelo", "m2", "--modelo", "m3",
                   "--modelo", "m4", "--modelo", "m5", "--modelo", "m6"])
