"""Permisos en servidor: IA/agentes, herramientas, conexiones, pendientes, salas y MCP cliente; una prueba por cada ON/OFF."""
import json
import os
import pathlib
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from mvp import app as servicio, control

CAB = {"x-api-key": "api-ficticia"}


class Banco:
    def __init__(self, **datos):
        self.datos = dict(datos)
    def leer(self, nombre):
        return self.datos.get(nombre)
    def guardar(self, nombre, valor):
        if not nombre.isidentifier() or not isinstance(valor, str):
            raise ValueError("nombre invalido")
        self.datos[nombre] = valor


class MCPFalso(BaseHTTPRequestHandler):
    recibidas = []
    def log_message(self, *a): pass
    def do_POST(self):
        doc = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        MCPFalso.recibidas.append((doc["method"], self.headers.get("Authorization")))
        if self.headers.get("Authorization") != "Bearer secreto-externo":
            self.send_response(401); self.end_headers(); return
        if doc["method"] == "tools/list":
            res = {"tools": [{"name": "saluda", "description": "Saluda", "inputSchema": {"type": "object", "properties": {"quien": {"type": "string"}}}}]}
        elif doc["method"] == "tools/call":
            res = {"content": [{"type": "text", "text": "hola " + doc["params"]["arguments"].get("quien", "")}]}
        else:
            res = {}
        cuerpo = json.dumps({"jsonrpc": "2.0", "id": doc["id"], "result": res}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(cuerpo)


class Base(unittest.TestCase):
    def setUp(self):
        self.nube = {}
        def guardar(clave, nombre, valor):
            self.nube[nombre] = valor; return {"ok": True}
        def leer(clave, nombre):
            if nombre not in self.nube: raise RuntimeError("fallo de lectura HF")
            return {"ok": True, "valor": self.nube[nombre]}
        self.parches = [patch("mvp.app.hf_store.guardar", guardar), patch("mvp.app.hf_store.leer", leer),
                        patch.dict(os.environ, {"RIU_API_KEY": "api-ficticia", "MVP_MCP_LOCAL": "1"})]
        for p in self.parches: p.start()
        self.banco = Banco(HF_TOKEN="hf-ficticio", GITHUB_TOKEN="gh-principal", QWEN_API_KEY="qwen-ficticia")
        self.antes = getattr(servicio.app.state, "banco", None)
        servicio.app.state.banco = self.banco
        self.reiniciar()
        self.client = TestClient(servicio.app)

    def reiniciar(self):
        servicio.CONTROL.d, servicio.CONTROL.sincronizado, servicio.CONTROL.persistente = control._vacio(), False, False

    def tearDown(self):
        self.client.close(); servicio.app.state.banco = self.antes
        for p in self.parches: p.stop()
        self.reiniciar()

    def accion(self, nombre, cuerpo=None, codigo=200):
        r = self.client.post("/plugins/puente_chat/call/" + nombre, json=cuerpo or {}, headers=CAB)
        self.assertEqual(r.status_code, codigo, r.text)
        return r.json().get("result") if codigo == 200 else r.json()

    def mcp(self, metodo, params=None):
        d = {"jsonrpc": "2.0", "id": 1, "method": metodo}
        if params is not None: d["params"] = params
        return self.client.post("/mcp", json=d, headers=CAB).json()

    def llamar(self, nombre, args):
        return self.mcp("tools/call", {"name": nombre, "arguments": args})

    def nombres(self):
        return {t["name"] for t in self.mcp("tools/list")["result"]["tools"]}


class TestIA(Base):
    def chat(self, herramienta, flags=True):
        salida = {"texto": "", "tool_calls": [{"id": "1", "function": {"name": herramienta, "arguments": "{}"}}], "finish_reason": "tool_calls"}
        with patch("mvp.app.compute.llamar", return_value=salida):
            return self.client.post("/chat", headers=CAB, json={"mensajes": [{"role": "user", "content": "x"}], "tools": flags, "agente_tool": flags, "llm_tool": flags})

    def test_ia_apagada_por_defecto_y_bloquea_aunque_el_cliente_diga_on(self):
        self.assertEqual(self.accion("agent_access_lock")["locked"], True)
        for nombre in ("groq_agente", "llm", "nvidia_codigo", "agente_enlazar"):
            r = self.chat(nombre)
            self.assertEqual(r.status_code, 403, nombre)
            self.assertIn("ia=false", r.json()["detail"])

    def test_ia_on_permite_y_off_vuelve_a_bloquear_y_persiste(self):
        self.assertEqual(self.accion("agent_access_lock", {"locked": False})["locked"], False)
        self.assertEqual(self.chat("groq_agente").status_code, 200)
        self.assertEqual(self.chat("llm", flags=False).status_code, 403)  # el cliente tambien puede negar
        self.assertEqual(json.loads(self.nube[control.NOMBRE])["ia"], True)
        self.accion("agent_access_lock", {"locked": True})
        self.assertEqual(self.chat("groq_agente").status_code, 403)
        self.assertEqual(json.loads(self.nube[control.NOMBRE])["ia"], False)

    def test_estado_sobrevive_a_reinicio(self):
        self.accion("agent_access_lock", {"locked": False})
        self.reiniciar()
        self.assertEqual(self.accion("agent_access_lock")["locked"], False)

    def test_locked_debe_ser_booleano_y_requiere_clave(self):
        self.accion("agent_access_lock", {"locked": "no"}, 400)
        self.assertEqual(self.client.post("/plugins/puente_chat/call/agent_access_lock", json={"locked": False}).status_code, 401)
        self.assertEqual(self.accion("agent_access_lock")["locked"], True)

    def test_ia_off_no_bloquea_github_ni_hf(self):
        self.assertEqual(self.chat("github_leer", flags=False).status_code, 200)
        self.assertEqual(self.chat("almacen", flags=False).status_code, 200)

    def test_sin_estado_hf_sigue_en_memoria_y_lo_avisa(self):
        with patch("mvp.app.hf_store.guardar", side_effect=RuntimeError("fallo de escritura HF")):
            r = self.accion("agent_access_lock", {"locked": False})
        self.assertEqual((r["locked"], r["persistente"]), (False, False))


class TestHerramientas(Base):
    def test_lista_con_on_off_individual_y_servidor_las_aplica(self):
        tools = {t["nombre"]: t for t in self.accion("tools_lock")["tools"]}
        self.assertFalse(tools["github_leer"]["locked"])
        self.assertIn("github_leer", self.nombres())
        cambio = self.accion("tools_lock", {"tool": "github_leer", "locked": True})
        self.assertEqual((cambio["tool"], cambio["locked"]), ("github_leer", True))  # contrato que lee tools-ventana.js
        self.assertNotIn("github_leer", self.nombres())  # al modelo solo se le muestran las encendidas
        r = self.llamar("github_leer", {"repo": "x"})
        self.assertIn("bloqueada", r["error"]["message"])  # y se comprueba otra vez al ejecutar
        self.assertIn("herramienta=false", r["error"]["message"])
        self.accion("tools_lock", {"tool": "github_leer", "locked": False})
        self.assertIn("github_leer", self.nombres())

    def test_chat_ve_bloqueo_de_herramienta_apagada(self):
        self.accion("tools_lock", {"tool": "almacen", "locked": True})
        salida = {"texto": "", "tool_calls": [{"id": "1", "function": {"name": "almacen", "arguments": "{}"}}], "finish_reason": "tool_calls"}
        with patch("mvp.app.compute.llamar", return_value=salida):
            r = self.client.post("/chat", headers=CAB, json={"mensajes": [{"role": "user", "content": "x"}]})
        self.assertEqual(r.status_code, 403)

    def test_herramienta_desconocida_y_tipos(self):
        self.accion("tools_lock", {"tool": "inventada", "locked": True}, 400)
        self.accion("tools_lock", {"tool": "github_leer", "locked": "si"}, 400)

    def test_conexion_apagada_oculta_sus_herramientas(self):
        self.accion("conexiones", {"accion": "activar", "servicio": "github", "id": "defecto", "on": False})
        self.assertFalse({"github_leer", "github_escribir", "github_api"} & self.nombres())
        self.assertIn("almacen", self.nombres())  # otra conexion: otro permiso
        self.assertIn("conexion=false", self.llamar("github_leer", {"repo": "x"})["error"]["message"])

    def test_tres_permisos_separados(self):
        ok = lambda n, c=None: servicio.CONTROL.decidir(n, c)[0]  # noqa: E731
        todo = {"tools": True, "agente_tool": True, "llm_tool": True}
        self.assertFalse(ok("llm", todo))  # delegacion ia OFF
        self.accion("agent_access_lock", {"locked": False})
        self.assertTrue(ok("llm", todo))
        self.accion("tools_lock", {"tool": "llm", "locked": True})
        self.assertFalse(ok("llm", todo))  # herramienta OFF pese a delegacion ON
        self.accion("tools_lock", {"tool": "llm", "locked": False})
        self.accion("agent_access_lock", {"locked": True})
        self.assertTrue(ok("github_leer"))  # la delegacion no gobierna GitHub


class TestConexiones(Base):
    def test_varias_credenciales_por_servicio_con_on_off_y_sin_filtrar_secretos(self):
        r = self.accion("conexiones", {"accion": "agregar", "servicio": "github", "etiqueta": "Trabajo", "secreto": "gh-trabajo-1"})
        self.assertNotIn("gh-trabajo-1", json.dumps(r))
        self.assertNotIn("gh-trabajo-1", self.nube.get(control.NOMBRE, ""))
        gh = next(s for s in r["servicios"] if s["servicio"] == "github")["conexiones"]
        self.assertEqual([c["on"] for c in gh], [True, True])
        nueva = gh[1]["id"]
        self.assertEqual(servicio.CONTROL.credencial("github", self.banco), "gh-principal")
        self.accion("conexiones", {"accion": "activar", "servicio": "github", "id": "defecto", "on": False})
        self.assertEqual(servicio.CONTROL.credencial("github", self.banco), "gh-trabajo-1")  # usa la primera ON
        self.accion("conexiones", {"accion": "activar", "servicio": "github", "id": nueva, "on": False})
        with self.assertRaises(RuntimeError):
            servicio.CONTROL.credencial("github", self.banco)  # todas OFF: ninguna ejecucion
        self.assertEqual(servicio.CONTROL.credencial("hf", self.banco), "hf-ficticio")

    def test_validaciones(self):
        self.accion("conexiones", {"accion": "agregar", "servicio": "fax", "secreto": "x"}, 400)
        self.accion("conexiones", {"accion": "agregar", "servicio": "correo", "etiqueta": "a"}, 400)  # falta secreto
        self.accion("conexiones", {"accion": "activar", "servicio": "github", "id": "nope", "on": True}, 400)
        self.accion("conexiones", {"accion": "activar", "servicio": "github", "id": "defecto", "on": "si"}, 400)
        r = self.accion("conexiones", {})
        self.assertEqual({s["servicio"] for s in r["servicios"]}, {"github", "hf", "correo", "mcp", "otros"})

    def test_hf_almacen_usa_conexion_on_y_el_estado_no_depende_de_ella(self):
        self.accion("conexiones", {"accion": "agregar", "servicio": "hf", "etiqueta": "Otra", "secreto": "hf-otra"})
        self.accion("conexiones", {"accion": "activar", "servicio": "hf", "id": "defecto", "on": False})
        self.assertIn("almacen", self.nombres())
        usados = []
        with patch("mvp.app.hf_store.guardar", lambda clave, n, v: usados.append(clave) or {"ok": True}):
            self.client.post("/almacen", headers=CAB, json={"accion": "guardar", "destino": "hf", "nombre": "a.txt", "valor": "v"})
        self.assertEqual(usados, ["hf-otra"])
        for c in servicio.CONTROL.d["conexiones"]["hf"]:
            self.accion("conexiones", {"accion": "activar", "servicio": "hf", "id": c["id"], "on": False})
        self.assertNotIn("almacen", self.nombres())
        self.assertEqual(self.client.post("/almacen", headers=CAB, json={"accion": "leer", "destino": "hf", "nombre": control.NOMBRE}).status_code, 200)


class TestPendientes(Base):
    def test_checklist_completo_por_ui(self):
        a = self.accion("checklist", {"accion": "agregar", "texto": "uno"})["pendientes"][0]["id"]
        b = self.accion("checklist", {"accion": "agregar", "texto": "dos"})["pendientes"][1]["id"]
        self.assertTrue(self.accion("checklist", {"accion": "marcar", "id": a})["pendientes"][0]["hecho"])
        self.assertFalse(self.accion("checklist", {"accion": "marcar", "id": a, "hecho": False})["pendientes"][0]["hecho"])
        self.assertEqual([p["texto"] for p in self.accion("checklist", {"accion": "ordenar", "ids": [b, a]})["pendientes"]], ["dos", "uno"])
        self.accion("checklist", {"accion": "ordenar", "ids": [a]}, 400)
        self.assertEqual(len(self.accion("checklist", {"accion": "quitar", "id": a})["pendientes"]), 1)
        self.accion("checklist", {"accion": "agregar", "texto": " "}, 400)
        self.reiniciar()
        self.assertEqual([p["texto"] for p in self.accion("checklist")["pendientes"]], ["dos"])

    def test_modelo_consulta_y_actualiza_con_herramienta_habilitada(self):
        self.assertIn("pendientes", self.nombres())
        self.llamar("pendientes", {"accion": "agregar", "texto": "desde el modelo"})
        r = self.llamar("pendientes", {"accion": "listar"})["result"]["structuredContent"]["pendientes"]
        self.assertEqual(r[0]["texto"], "desde el modelo")
        self.assertEqual(self.accion("checklist")["pendientes"][0]["texto"], "desde el modelo")
        self.accion("tools_lock", {"tool": "pendientes", "locked": True})
        self.assertNotIn("pendientes", self.nombres())
        self.assertIn("herramienta=false", self.llamar("pendientes", {"accion": "agregar", "texto": "otro"})["error"]["message"])
        self.assertEqual(len(self.accion("checklist")["pendientes"]), 1)


class TestSalas(Base):
    def test_salas_permisos_de_acceso(self):
        sid = self.accion("salas", {"accion": "crear", "nombre": "Reunion", "participantes": {"ana": "escritura"}})["salas"][0]["id"]
        self.assertEqual(self.llamar("sala", {"accion": "listar"})["result"]["structuredContent"]["salas"], [])  # el modelo no esta
        negado = self.llamar("sala", {"accion": "leer", "id": sid})
        self.assertIn("sala desconocida", negado["error"]["message"])
        self.accion("salas", {"accion": "permiso", "id": sid, "participante": "modelo", "nivel": "lectura"})
        self.assertEqual(self.llamar("sala", {"accion": "leer", "id": sid})["result"]["structuredContent"]["sala"]["nombre"], "Reunion")
        escribir = self.llamar("sala", {"accion": "enviar", "id": sid, "texto": "hola"})["result"]
        self.assertTrue(escribir["isError"])
        self.assertIn("acceso denegado", escribir["content"][0]["text"])
        self.accion("salas", {"accion": "permiso", "id": sid, "participante": "modelo", "nivel": "escritura"})
        self.llamar("sala", {"accion": "enviar", "id": sid, "texto": "hola equipo"})
        self.llamar("sala", {"accion": "contexto", "id": sid, "texto": "tema: roadmap"})
        sala = self.accion("salas", {"accion": "leer", "id": sid})["sala"]
        self.assertEqual((sala["mensajes"][0]["de"], sala["mensajes"][0]["texto"], sala["contexto"]), ("modelo", "hola equipo", "tema: roadmap"))
        self.assertTrue(self.llamar("sala", {"accion": "permiso", "id": sid, "participante": "ana", "nivel": "admin"})["result"]["isError"])  # sin admin
        self.accion("salas", {"accion": "enviar", "id": sid, "texto": "ok", "de": "ana"})
        self.assertEqual(len(self.accion("salas", {"accion": "leer", "id": sid})["sala"]["mensajes"]), 2)
        self.accion("salas", {"accion": "borrar", "id": sid})
        self.assertEqual(self.accion("salas")["salas"], [])

    def test_sala_como_herramienta_on_off_y_validaciones(self):
        self.assertIn("sala", self.nombres())
        self.accion("tools_lock", {"tool": "sala", "locked": True})
        self.assertNotIn("sala", self.nombres())
        self.assertIn("herramienta=false", self.llamar("sala", {"accion": "listar"})["error"]["message"])
        self.accion("salas", {"accion": "crear", "nombre": ""}, 400)
        self.accion("salas", {"accion": "crear", "nombre": "x", "participantes": {"a": "dios"}}, 400)
        self.accion("salas", {"accion": "enviar", "id": "nope", "texto": "x"}, 400)


class TestMCPCliente(Base):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), MCPFalso)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d/mcp" % cls.http.server_port
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close()

    def agregar(self, secreto="secreto-externo"):
        r = self.accion("conexiones", {"accion": "agregar", "servicio": "mcp", "etiqueta": "Ext", "url": self.url, "secreto": secreto})
        return next(s for s in r["servicios"] if s["servicio"] == "mcp")["conexiones"][0], r

    def test_cliente_descubre_ejecuta_en_servidor_y_respeta_on_off(self):
        con, r = self.agregar()
        self.assertNotIn("secreto-externo", json.dumps(r))
        self.assertEqual(con["herramientas"], ["saluda"])
        nombre = "mcp__%s__saluda" % con["id"]
        self.assertNotIn(nombre, self.nombres())  # herramientas externas arrancan apagadas
        self.assertIn("herramienta=false", self.llamar(nombre, {"quien": "x"})["error"]["message"])
        self.accion("tools_lock", {"tool": nombre, "locked": False})
        self.assertIn(nombre, self.nombres())
        ok = self.llamar(nombre, {"quien": "Luna"})["result"]
        self.assertEqual((ok["content"][0]["text"], ok["isError"]), ("hola Luna", False))
        self.assertIn(("tools/call", "Bearer secreto-externo"), MCPFalso.recibidas)  # el token lo pone el servidor
        self.accion("conexiones", {"accion": "activar", "servicio": "mcp", "id": con["id"], "on": False})
        self.assertNotIn(nombre, self.nombres())
        self.assertIn("conexion=false", self.llamar(nombre, {"quien": "x"})["error"]["message"])

    def test_autenticacion_incorrecta_y_urls_peligrosas(self):
        r = self.accion("conexiones", {"accion": "agregar", "servicio": "mcp", "etiqueta": "Mal", "url": self.url, "secreto": "incorrecto"})
        self.assertIn("401", r["aviso"])
        with patch.dict(os.environ, {"MVP_MCP_LOCAL": "0"}):
            r = self.accion("conexiones", {"accion": "agregar", "servicio": "mcp", "etiqueta": "Http", "url": self.url})
            self.assertIn("HTTPS", r["aviso"])
            r = self.accion("conexiones", {"accion": "agregar", "servicio": "mcp", "etiqueta": "Priv", "url": "https://127.0.0.1/mcp"})
            self.assertIn("red privada", r["aviso"])

    def test_servidor_mcp_expone_herramientas_del_chat_y_ROOM(self):
        self.assertTrue({"pendientes", "sala", "github_leer", "almacen"} <= self.nombres())


class TestPersistencia(unittest.IsolatedAsyncioTestCase):
    async def test_ida_y_vuelta_y_fallo_de_lectura(self):
        guardado = {}
        async def guardar(texto): guardado["v"] = texto
        async def leer(): return guardado["v"]
        a = control.Control(); a.conectar(leer, guardar)
        await a.aplicar("agent_access_lock", {"locked": False})
        await a.aplicar("checklist", {"accion": "agregar", "texto": "p"})
        b = control.Control(); b.conectar(leer, guardar)
        await b.cargar()
        self.assertEqual((b.d["ia"], b.d["pendientes"][0]["texto"], b.persistente), (True, "p", True))
        async def roto(): raise RuntimeError("HF caido")
        c = control.Control(); c.conectar(roto, guardar)
        await c.cargar()
        self.assertEqual((c.d["ia"], c.persistente), (False, False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
