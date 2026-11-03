"""Contrato de acceso GitHub/Hugging Face para modelos del Router; sin red ni tokens reales."""
import base64
import json
from unittest.mock import patch

from plugins.puente_chat import herramientas as h


def test_herramientas_read_only_de_salud_para_modelos():
    nombres = {(x.get("function") or {}).get("name") for x in h.TOOLS}
    assert {"github_salud", "hf_salud", "github_leer", "github_escribir", "hf_leer", "hf_escribir"} <= nombres
    assert "rama main" in h.SISTEMA
    assert "Nunca pidas pegar tokens en el chat" in h.SISTEMA


def test_lectura_y_escritura_tienen_main_por_defecto_sin_modificar_otras_ramas():
    rutas = []
    contenido = base64.b64encode(b"PASS repositorio").decode()
    def gh(metodo, ruta, cuerpo=None):
        rutas.append((metodo, ruta))
        if metodo == "GET":
            return 200, {"encoding": "base64", "content": contenido, "sha": "sha-de-prueba"}
        return 200, {"commit": {"sha": "commit-prueba"}}
    with patch.object(h, "_gh", side_effect=gh):
        assert h.github_leer({"repo": "Maxbry-AGI", "ruta": "README.md"}) == "PASS repositorio"
        assert "ref=main" in rutas[0][1]
        assert "ref=reorganizacion" not in rutas[0][1]


def test_github_salud_detecta_permisos_por_repo_y_nunca_exhibe_token():
    with patch.object(h, "_resolver_repo", side_effect=lambda x: x), \
         patch.object(h, "_token_gh", side_effect=lambda repo, escritura=False: "" if escritura else "credencial-ficticia-solo-test"), \
         patch.object(h, "_peticion", return_value=(200, {"permissions": {"pull": True, "push": False}})):
        r = h.github_salud({"repo": "Maxbry-AGI"})
    assert r["authenticated"] is True and r["read"] is True and r["push"] is False
    assert r["causa"] == "SOLO_LECTURA"
    assert "credencial-ficticia" not in json.dumps(r)
    with patch.object(h, "_resolver_repo", side_effect=lambda x: x), patch.object(h, "_token_gh", return_value=""):
        r = h.github_salud({"repo": "Maxbry-AGI"})
    assert r["authenticated"] is False and r["causa"] == "CONECTAR_GITHUB_EN_BANCO"


def test_hf_salud_verifica_lectura_sin_inventar_permiso_escritura():
    with patch.object(h, "_token_hf", return_value="token-ficticio-solo-test"), \
         patch.object(h, "_peticion", return_value=(200, {"id": "COMAND-CENTER-1/riu-router"})):
        r = h.hf_salud({"repo": "COMAND-CENTER-1/riu-router", "tipo": "space"})
    assert r["authenticated"] is True and r["lectura"] is True and r["escritura"] == "SIN_VERIFICAR"
    assert "token-ficticio" not in json.dumps(r)
    with patch.object(h, "_token_hf", return_value=""):
        r = h.hf_salud({"repo": "COMAND-CENTER-1/riu-router", "tipo": "space"})
    assert r["causa"] == "CONECTAR_HF_EN_BANCO"
    assert h.hf_salud({"repo": "x/y", "tipo": "invalid"})["causa"] == "TIPO_INVALIDO"


def test_otro_owner_no_queda_autorizado_por_supuesto():
    code, detalle = h._gh("GET", "/repos/otro-usuario/privado")
    assert code == 0 and "no permitida" in detalle.lower()
