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
            self.assertIn("agentes=false" if nombre in ("groq_agente", "agente_enlazar") else "ia=false", r.json()["detail"])

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

    def test_quitar_conexion_libera_hueco_y_borra_su_secreto(self):
        r = self.accion("conexiones", {"accion": "agregar", "servicio": "github", "etiqueta": "otra", "secreto": "gh-otra"})
        cid = next(x["id"] for s in r["servicios"] if s["servicio"] == "github" for x in s["conexiones"] if x["etiqueta"] == "otra")
        r = self.accion("conexiones", {"accion": "quitar", "servicio": "github", "id": cid})
        self.assertNotIn(cid, [x["id"] for s in r["servicios"] for x in s["conexiones"]])
        self.assertEqual(self.banco.leer("CONN_GITHUB_" + cid), "")
        self.accion("conexiones", {"accion": "quitar", "servicio": "github", "id": "defecto"}, 400)  # la principal del banco no se quita

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


class TestEspacio(Base):
    def subir(self, nombre="notas.txt", texto="contenido de prueba", **extra):
        import base64
        return self.accion("subir", {"nombre": nombre, "tipo": "texto", "datos_b64": base64.b64encode(texto.encode()).decode(), "sesion": "s1", **extra})

    def test_status_estado_y_herramientas_estado(self):
        self.assertEqual(self.accion("status")["servicio"], "router_mvp")
        self.assertIn("commit", self.accion("status"))
        e = self.accion("estado", {"sesion": "s1"})
        self.assertEqual((e["sesion"], e["ia"], e["conexiones_on"]["github"]), ("s1", False, 1))
        self.assertIn("github_leer", {t["nombre"] for t in self.accion("herramientas_estado")["tools"]})

    def test_archivos_subir_listar_borrar_restaurar(self):
        self.assertEqual(self.accion("archivos", {"sesion": "s1"}), {"archivos": [], "persistente": False})
        self.assertEqual(self.subir()["nombre"], "notas.txt")
        self.assertEqual(self.accion("archivos", {"sesion": "s1"})["archivos"], ["notas.txt"])
        self.assertEqual(self.accion("archivos", {"sesion": "otra"})["archivos"], [])  # cada chat su carpeta
        self.assertEqual(self.accion("archivos", {"sesion": "s1", "destino": "proyecto", "project_id": "p-1"})["archivos"], [])
        self.accion("archivo_borrar", {"nombre": "notas.txt", "sesion": "s1"})
        self.assertEqual(self.accion("archivos", {"sesion": "s1"})["archivos"], [])
        self.accion("archivo_borrar", {"nombre": "notas.txt", "sesion": "s1", "restaurar": True})
        self.assertEqual(self.accion("archivos", {"sesion": "s1"})["archivos"], ["notas.txt"])
        self.accion("archivo_borrar", {"nombre": "nope.txt", "sesion": "s1"}, 400)

    def test_subir_valida_y_no_deja_fantasmas(self):
        self.accion("subir", {"nombre": "../x.txt", "datos_b64": "aG9sYQ==", "sesion": "s1"}, 400)
        self.accion("subir", {"nombre": "a.txt", "datos_b64": "###", "sesion": "s1"}, 400)
        self.accion("subir", {"nombre": "a.txt", "datos_b64": "", "sesion": "s1"}, 400)
        def rechaza_codigo(clave, nombre, valor):  # hf_store._ruta no admite .py/.js/...
            raise ValueError("ID HF no permitido")
        with patch("mvp.app.hf_store.guardar", rechaza_codigo):
            r = self.client.post("/plugins/puente_chat/call/subir", headers=CAB, json={"nombre": "codigo.py", "datos_b64": "aG9sYQ==", "sesion": "s1"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("GitHub", r.json()["detail"])
        self.assertEqual(self.accion("archivos", {"sesion": "s1"})["archivos"], [])  # nada registrado si no se guardó

    def test_sandbox_encender_y_apagar(self):
        self.assertEqual(self.accion("sandbox", {"sesion": "s1"})["encendido"], False)
        r = self.accion("sandbox", {"sesion": "s1", "texto": "eres un revisor de código"})
        self.assertEqual((r["encendido"], r["sandbox"]), (True, "eres un revisor de código"))
        self.assertEqual(self.accion("sandbox", {"sesion": "otra"})["sandbox"], "")
        self.assertEqual(self.accion("sandbox", {"sesion": "s1", "texto": ""})["encendido"], False)
        self.accion("sandbox", {"sesion": "s1", "texto": 5}, 400)

    def test_yaiwes_md_y_sandbox_viajan_con_el_mensaje(self):
        self.assertEqual(self.accion("handoff_texto", {"sesion": "s1"}), {"texto": "", "encendido": False, "persistente": False})
        self.assertTrue(self.accion("handoff_texto", {"sesion": "s1", "texto": "trabaja en el repo X"})["encendido"])
        self.accion("sandbox", {"sesion": "s1", "texto": "eres revisor"})
        self.banco.datos["RIU_API_KEY"] = "clave-harness"
        salida = {"texto": "ok", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "x"}
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", return_value={"status": "ok", "result": salida}) as llm:
            self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "qwen3.8-max", "sesion": "s1"})
            self.assertIn("trabaja en el repo X", json.dumps(llm.call_args.args[1]))
            self.assertIn("eres revisor", json.dumps(llm.call_args.args[1]))
            self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "qwen3.8-max", "sesion": "otra"})
            self.assertIn("trabaja en el repo X", json.dumps(llm.call_args.args[1]))  # yaiwes.md es global: lo ven todos los chats
            self.assertNotIn("eres revisor", json.dumps(llm.call_args.args[1]))  # el sandbox es de cada chat
        self.assertFalse(self.accion("handoff_texto", {"sesion": "s1", "texto": ""})["encendido"])

    def test_prompt_organizador_y_constitucion(self):
        self.assertTrue(self.accion("agent_access_lock", {"quien": "prompt"})["prompt_locked"])  # nace OFF
        self.assertFalse(self.accion("agent_access_lock", {"quien": "prompt", "locked": False})["prompt_locked"])
        a = self.accion("checklist", {"accion": "agregar", "texto": "uno"})["pendientes"][0]["id"]
        b = self.accion("checklist", {"accion": "agregar", "texto": "dos"})["pendientes"][1]["id"]
        self.banco.datos["QWEN_API_KEY"] = "k"
        with patch("mvp.app.compute.llamar", return_value={"texto": '["%s", "zzzzzzzz", "%s"]' % (b, b)}):
            orden = self.accion("checklist", {"accion": "organizar"})["pendientes"]
        self.assertEqual([x["id"] for x in orden], [b, a])  # ids inventados o repetidos se ignoran; ninguno se pierde
        self.banco.datos["RIU_API_KEY"] = "clave-harness"
        salida = {"texto": "ok", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "x"}
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", return_value={"status": "ok", "result": salida}) as llm:
            self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "qwen3.8-max", "sesion": "s1"})
            self.assertIn("dos", json.dumps(llm.call_args.args[1]))  # la lista de pendientes viaja al modelo

    def test_proyectos(self):
        p = self.accion("proyecto", {"op": "upsert", "project_id": "p-1", "nombre": "Uno"})["proyecto"]
        self.assertEqual(p["nombre"], "Uno")
        self.accion("proyecto", {"op": "upsert", "project_id": "p-1", "notas": "n"})  # merge: conserva el nombre
        self.assertEqual(self.accion("proyecto", {"op": "get", "project_id": "p-1"})["proyecto"]["nombre"], "Uno")
        self.assertEqual(self.accion("proyecto", {"op": "link_chat", "project_id": "p-1", "sesion": "s1"})["proyecto"]["chats"], ["s1"])
        self.assertEqual(self.accion("proyecto", {"op": "unlink_chat", "project_id": "p-1", "sesion": "s1"})["proyecto"]["chats"], [])
        self.assertEqual(len(self.accion("proyecto", {"op": "list"})["proyectos"]), 1)
        self.accion("proyecto", {"op": "upsert", "project_id": "../x"}, 400)
        self.accion("proyecto", {"op": "get", "project_id": "nada"}, 400)
        self.accion("proyecto", {"op": "delete", "project_id": "p-1"})
        self.assertEqual(self.accion("proyecto")["proyectos"], [])

    def test_los_anclados_llegan_al_modelo_y_los_secretos_no(self):
        self.subir("notas.txt", "el codigo del proyecto es AZUL-7")
        self.banco.datos["RIU_API_KEY"] = "clave-harness"
        salida = {"texto": "ok", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "x"}
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", return_value={"status": "ok", "result": salida}) as llm:
            r = self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "qwen3.8-max", "sesion": "s1",
                                                                  "anclados": ["notas.txt", "texto:recuerda ser breve", "secreto:hf/token", "no-existe.txt"]})
        self.assertEqual(r.status_code, 200)
        enviado = json.dumps(llm.call_args.args[1], ensure_ascii=False)
        self.assertIn("AZUL-7", enviado)
        self.assertIn("recuerda ser breve", enviado)
        self.assertNotIn("hf/token", enviado)
        self.assertNotIn("no-existe", enviado)


class TestAgentes(Base):
    def falso(self):
        return patch("mvp.app.compute.llamar", return_value={"texto": "respuesta del agente", "tool_calls": [], "finish_reason": "stop"})

    def test_dos_botones_separados_ia_y_agentes(self):
        self.assertEqual((self.accion("agent_access_lock")["ia_locked"], self.accion("agent_access_lock")["agentes_locked"]), (True, True))
        r = self.accion("agent_access_lock", {"locked": False, "quien": "agentes"})
        self.assertEqual((r["ia_locked"], r["agentes_locked"], r["locked"]), (True, False, False))
        self.assertTrue({"agente"} <= self.nombres() and "llm" not in self.nombres())  # el modelo solo ve lo que esta encendido
        r = self.accion("agent_access_lock", {"locked": False, "quien": "ia"})
        self.assertTrue({"agente", "llm"} <= self.nombres())
        self.accion("agent_access_lock", {"locked": True, "quien": "agentes"})
        self.assertTrue("agente" not in self.nombres() and "llm" in self.nombres())
        self.accion("agent_access_lock", {"locked": True, "quien": "otro"}, 400)

    def test_conectar_1_o_50_agentes_con_su_modelo(self):
        e = self.accion("tools_estado")
        self.assertEqual((e["agentes"], e["max"], len(e["recursos"])), ([], 50, 12))
        e = self.accion("agente_enlazar", {"nombre": "Revisor", "recurso": "qwen3.7-plus", "sistema": "revisa codigo"})
        self.assertEqual([(a["nombre"], a["recurso"]) for a in e["agentes"]], [("Revisor", "qwen3.7-plus")])
        e = self.accion("agente_enlazar", {"nombre": "Revisor", "recurso": "glm-5.3"})  # cambiar solo el modelo conserva las instrucciones
        self.assertEqual((e["agentes"][0]["recurso"], e["agentes"][0]["sistema"]), ("glm-5.3", "revisa codigo"))
        self.accion("agente_enlazar", {"nombre": "", "recurso": "glm-5.3"}, 400)
        self.accion("agente_enlazar", {"nombre": "X", "recurso": "qwen-image-3.0-pro"}, 400)  # solo modelos de texto
        lista = [{"nombre": "A%d" % i, "recurso": "qwen3.8-flash"} for i in range(50)]
        self.assertEqual(len(self.accion("groq_agentes", {"agentes": lista})["agentes"]), 50)
        self.accion("agente_enlazar", {"nombre": "uno-mas", "recurso": "glm-5.3"}, 400)  # el 51 no entra
        self.assertEqual(len(self.accion("groq_agentes", {"agentes": lista[:2]})["agentes"]), 2)
        self.reiniciar()
        self.assertEqual(len(self.accion("tools_estado")["agentes"]), 2)  # persiste por /almacen

    def test_el_modelo_llama_al_agente_como_sesion_nueva(self):
        self.accion("agente_enlazar", {"nombre": "Revisor", "recurso": "qwen3.7-plus", "sistema": "revisa codigo"})
        self.assertIn("bloqueada", self.llamar("agente", {"nombre": "Revisor", "mensaje": "hola"})["error"]["message"])  # apagado
        self.accion("agent_access_lock", {"locked": False, "quien": "agentes"})
        with self.falso() as llm:
            r = self.llamar("agente", {"nombre": "Revisor", "mensaje": "mira esto"})["result"]["structuredContent"]
        self.assertEqual((r["texto"], r["modelo"]), ("respuesta del agente", "qwen3.7-plus"))
        msgs = llm.call_args.args[0]
        self.assertEqual([(m["role"], m["content"]) for m in msgs], [("system", "revisa codigo"), ("user", "mira esto")])  # sin historial ni herramientas
        self.assertEqual(llm.call_args.args[1], "qwen3.7-plus")
        self.assertIn("agente desconocido", self.llamar("agente", {"nombre": "Nadie", "mensaje": "x"})["error"]["message"])

    def test_el_modelo_llama_a_otro_modelo_solo_con_ia_encendida(self):
        self.accion("agent_access_lock", {"locked": False, "quien": "agentes"})
        self.assertIn("ia=false", self.llamar("llm", {"modelo": "glm-5.3", "mensaje": "x"})["error"]["message"])
        self.accion("agent_access_lock", {"locked": False, "quien": "ia"})
        with self.falso() as llm:
            r = self.llamar("llm", {"modelo": "glm-5.3", "mensaje": "hola"})["result"]["structuredContent"]
        self.assertEqual((r["modelo"], llm.call_args.args[1]), ("glm-5.3", "glm-5.3"))
        self.assertIn("modelo no permitido", self.llamar("llm", {"modelo": "no-existe", "mensaje": "x"})["error"]["message"])

    def test_probar_un_recurso_o_un_agente_desde_el_panel(self):
        self.accion("agente_enlazar", {"nombre": "Revisor", "recurso": "qwen3.7-plus", "sistema": "s"})
        with self.falso():
            self.assertEqual(self.accion("recurso_probar", {"recurso": "glm-5.3"})["respuesta"], "respuesta del agente")
            self.assertTrue(self.accion("recurso_probar", {"agente": "Revisor"})["ok"])
        r = self.accion("recurso_probar", {"recurso": "no-existe"})
        self.assertEqual(r["ok"], False)


class TestGapsChat(Base):
    def test_selector_de_modelos_sale_solo_de_modelos_json(self):
        from mvp import modelos
        for plan in ("personal", "team"):
            with patch.dict(os.environ, {"MVP_PLAN": plan}):
                r = self.client.get("/chat/providers/qwen/models", headers=CAB).json()["models"]
                self.assertEqual([m["model_id"] for m in r], [i for i, _ in modelos.catalogo()])
                self.assertEqual(self.client.post("/chat", headers=CAB, json={"modelo": "no-existe", "mensajes": [{"role": "user", "content": "x"}]}).status_code, 400)
        with patch.dict(os.environ, {"MVP_PLAN": "personal"}):
            self.assertEqual(self.client.post("/chat", headers=CAB, json={"modelo": "qwen3.6-plus", "mensajes": [{"role": "user", "content": "x"}]}).status_code, 400)

    def test_limite_de_texto_y_finish_reason(self):
        enorme = [{"role": "user", "content": "a" * 1_000_001}]
        r = self.client.post("/chat", headers=CAB, json={"mensajes": enorme})
        self.assertEqual(r.status_code, 413)
        self.assertIn("caracteres", r.json()["detail"])
        corta = {"texto": "se cort", "tool_calls": [], "finish_reason": "length"}
        with patch("mvp.app.compute.llamar", return_value=corta):
            ok = self.client.post("/chat", headers=CAB, json={"mensajes": [{"role": "user", "content": "x"}]}).json()
        self.assertEqual((ok["texto"], ok["finish_reason"]), ("se cort", "length"))

    def test_ficha_heredada_del_chat_usa_modelo_por_defecto(self):
        salida = {"texto": "ok", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "x"}
        self.banco.datos["RIU_API_KEY"] = "clave-harness"
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", return_value={"status": "ok", "result": salida}) as llm:
            r = self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "nv-muse-glimmer"})
            self.assertEqual((r.status_code, llm.call_args.args[2]), (200, "qwen3.8-max"))
            r = self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "modelo-inexistente"})
            self.assertEqual(r.status_code, 400)

    def test_selector_pensar_llega_al_modelo(self):
        salida = {"texto": "ok", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "x"}
        self.banco.datos["RIU_API_KEY"] = "clave-harness"
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", return_value={"status": "ok", "result": salida}) as llm:
            for modo, esperado in (("on", True), ("off", False)):
                self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "qwen3.8-max", "thinking_mode": modo})
                self.assertEqual(llm.call_args.args[3], {"enable_thinking": esperado})
            self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "qwen3.8-flash", "thinking_mode": "on"})
            self.assertIsNone(llm.call_args.args[3] or None)

    def enviar_con_modo(self, **extra):
        salida = {"texto": "ok", "tool_calls": [], "finish_reason": "stop", "modelo_respuesta": "x"}
        self.banco.datos["RIU_API_KEY"] = "clave-harness"
        with patch.dict(os.environ, {"RIU_DEEPSEEK_HARNESS_URL": "http://127.0.0.1:1"}), patch("mvp.app.harness_client.llm", return_value={"status": "ok", "result": salida}) as llm:
            r = self.client.post("/chat/send", headers=CAB, json={"message": "hola", "model": "qwen3.8-max", **extra})
        return r, (llm.call_args.args[1] if llm.call_args else None)

    def test_motores_envuelven_el_system_prompt_por_modo(self):
        r, msgs = self.enviar_con_modo()  # Auto sin regla = modo por defecto: solo la capa de formato, sin el texto "sin herramientas" de m05
        self.assertEqual((r.status_code, [m["role"] for m in msgs], msgs[-1]), (200, ["system", "user"], {"role": "user", "content": "hola"}))
        self.assertIn("FORMATO DE SALIDA", msgs[0]["content"])
        self.assertNotIn("MODO ACTIVO", msgs[0]["content"])
        r, msgs = self.enviar_con_modo(mode_request={"mode_id": "m01_plan", "source": "button"})
        self.assertEqual(([m["role"] for m in msgs], msgs[-1]["content"]), (["system", "system", "user"], "hola"))
        self.assertIn("m01_plan", msgs[1]["content"])
        r, msgs = self.enviar_con_modo(message="investiga sobre qwen", mode_request={"mode_id": "auto", "source": "auto"})
        self.assertIn("m03_investigacion", msgs[1]["content"])  # Auto: lo decide la regla del clasificador
        r, msgs = self.enviar_con_modo(message="/auto  que tal", mode_request={"mode_id": "auto", "source": "auto"})
        self.assertEqual(msgs[-1]["content"], "que tal")  # el slash se quita del texto

    def test_modo_autonomo_y_modo_invalido_fallan_cerrados(self):
        r, msgs = self.enviar_con_modo(mode_request={"mode_id": "m04_agentico_loop", "source": "button"})
        self.assertEqual((r.status_code, msgs), (501, None))
        self.assertIn("m04_agentico_loop", r.json()["detail"])
        r, _ = self.enviar_con_modo(mode_request={"mode_id": "m01_plan", "source": "auto"})
        self.assertEqual(r.status_code, 400)
        r, _ = self.enviar_con_modo(mode_request={"mode_id": "m99", "source": "button"})
        self.assertEqual(r.status_code, 400)

    def test_cors_solo_para_el_chat_de_vercel(self):
        for origen, permitido in (("https://riu-jev-bridge.vercel.app", True), ("https://riu-jev-bridge-git-main-maxbry123-8833s-projects.vercel.app", True), ("https://malo.example.com", False)):
            r = self.client.options("/chat/send", headers={"Origin": origen, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-api-key,content-type"})
            self.assertEqual(r.headers.get("access-control-allow-origin") == origen, permitido, origen)

    def test_errores_del_proveedor_son_visibles(self):
        with patch("mvp.app.compute.llamar", side_effect=RuntimeError("Proveedor HTTP 500")):
            r = self.client.post("/chat", headers=CAB, json={"mensajes": [{"role": "user", "content": "x"}]})
        self.assertEqual((r.status_code, r.json()["detail"]), (502, "Proveedor HTTP 500"))


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


class TurnoSala(Base):
    def accion(self, nombre, cuerpo=None):
        r = self.client.post("/plugins/puente_chat/call/" + nombre, json=cuerpo or {}, headers=CAB)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json().get("result")

    def test_agentes_y_modelos_hablan_en_la_misma_sala(self):
        self.accion("agent_access_lock", {"quien": "todo", "locked": False})
        self.accion("agente_enlazar", {"op": "poner", "nombre": "Revisor", "recurso": "qwen3.7-plus", "sistema": "revisas"})
        sid = self.accion("salas", {"accion": "crear", "nombre": "Mesa", "participantes": {"Revisor": "escritura", "qwen3.8-flash": "escritura", "Mudo": "lectura"}})["salas"][0]["id"]
        self.accion("salas", {"accion": "enviar", "id": sid, "texto": "Opinen sobre el plan"})
        with patch("mvp.app.compute.llamar", side_effect=lambda m, mod, *a: {"texto": "aporte de " + mod}):
            r = self.accion("salas", {"accion": "turno", "id": sid})
        self.assertEqual(sorted(r["hablaron"]), ["Revisor", "qwen3.8-flash"])
        self.assertEqual([m["de"] for m in r["sala"]["mensajes"]][1:], r["hablaron"])
        self.accion("agent_access_lock", {"quien": "agentes", "locked": True})
        with patch("mvp.app.compute.llamar", return_value={"texto": "x"}):
            r = self.accion("salas", {"accion": "turno", "id": sid})
        self.assertEqual(r["hablaron"], ["qwen3.8-flash"]); self.assertEqual(r["saltadas"][0]["participante"], "Revisor")
