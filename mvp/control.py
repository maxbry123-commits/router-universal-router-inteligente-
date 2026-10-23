"""Permisos y estado del chat decididos en el servidor; el frontend solo los muestra.
Tres permisos separados: conexion ON, herramienta ON y delegacion IA ON (solo para herramientas que llaman IA/agentes).
El estado (sin secretos) se persiste por /almacen; los secretos de las conexiones viven en el banco cifrado."""
import json
import re
import time
import uuid

AGENTE_TOOLS = {"agente", "agent", "groq_agente", "agente_enlazar"}
LLM_TOOLS = {"chat", "llm", "recurso_llm", "nvidia_codigo"}
NOMBRE = "chat_estado/control.json"
SERVICIOS = {"github": "GitHub", "hf": "Hugging Face", "correo": "Correo", "mcp": "Servidor MCP", "otros": "Otros"}
LEGADO = {"github": "GITHUB_TOKEN", "hf": "HF_TOKEN"}  # credencial "defecto" de cada servicio: la que ya trae el banco
TOOLS = {"github_leer": ("GitHub", "github"), "github_escribir": ("GitHub", "github"), "github_api": ("GitHub", "github"),
         "almacen": ("Hugging Face", "hf"), "pendientes": ("Chat", None), "sala": ("Chat", None)}
NIVELES = {"lectura": 1, "escritura": 2, "admin": 3}
MCP = re.compile(r"mcp__([0-9a-f]{8})__([A-Za-z0-9_-]{1,49})")
MAX_CONEXIONES, MAX_PENDIENTES, MAX_SALAS, MAX_MENSAJES = 10, 200, 20, 500


def tipo(nombre):
    return "agente_tool" if nombre in AGENTE_TOOLS else "llm_tool" if nombre in LLM_TOOLS else None


def _vacio():
    base = {s: [] for s in SERVICIOS}
    for s in LEGADO:
        base[s].append({"id": "defecto", "etiqueta": "Principal (banco)", "on": True})
    return {"ia": False, "herramientas": {}, "conexiones": base, "pendientes": [], "salas": {}}


def _texto(valor, maximo, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(campo + " requerido")
    if len(valor) > maximo:
        raise ValueError(campo + " supera " + str(maximo) + " caracteres")
    return valor.strip()


def _booleano(valor, campo):
    if type(valor) is not bool:
        raise ValueError(campo + " debe ser booleano")
    return valor


class Control:
    def __init__(self):
        self.d, self.persistente, self.sincronizado, self._sucio = _vacio(), False, False, False
        self._leer = self._guardar = None

    def conectar(self, leer, guardar):
        self._leer, self._guardar = leer, guardar

    async def cargar(self):
        if not self._leer:
            return
        try:
            guardado = json.loads(await self._leer())
            if isinstance(guardado, dict):
                self.d = {**_vacio(), **{k: v for k, v in guardado.items() if k in _vacio()}}
                for s in LEGADO:
                    if not any(c["id"] == "defecto" for c in self.d["conexiones"].setdefault(s, [])):
                        self.d["conexiones"][s].insert(0, _vacio()["conexiones"][s][0])
            self.sincronizado = self.persistente = True
        except Exception:  # noqa: BLE001 - HF caido o estado inexistente: se sigue con el estado en memoria
            self.persistente = False

    async def persistir(self):
        if not self._guardar:
            return
        try:
            await self._guardar(json.dumps(self.d, ensure_ascii=False))
            self.persistente = True
        except Exception:  # noqa: BLE001
            self.persistente = False

    async def aplicar(self, accion, cuerpo, banco=None, actor="director"):
        if not self.sincronizado:
            await self.cargar()
        self._sucio = False
        salida = self.ejecutar(accion, cuerpo, banco, actor)
        if self._sucio:
            await self.persistir()
        return {**salida, "persistente": self.persistente}

    def ejecutar(self, accion, c, banco=None, actor="director"):
        if accion not in ACCIONES:
            raise ValueError("accion no soportada")
        return getattr(self, "_" + accion)(c if isinstance(c, dict) else {}, banco, actor)

    # --- decision unica: conexion + herramienta + delegacion ---
    def _mcp(self, nombre):
        m = MCP.fullmatch(nombre)
        con = next((c for c in self.d["conexiones"]["mcp"] if m and c["id"] == m.group(1)), None)
        return (con, m.group(2)) if con and any(h["nombre"] == m.group(2) for h in con.get("herramientas", [])) else None

    def decidir(self, nombre, controles=None):
        t, c = tipo(nombre), controles or {}
        if t:
            for falta in (("tools", c.get("tools")), (t, c.get(t)), ("ia", self.d["ia"])):
                if not falta[1]:
                    return False, falta[0] + "=false"
        if nombre.startswith("mcp__"):
            mcp = self._mcp(nombre)
            if not mcp or not mcp[0]["on"]:
                return False, "conexion=false"
            return (True, "") if self.d["herramientas"].get(nombre, False) else (False, "herramienta=false")
        if (nombre in TOOLS or t) and not self.d["herramientas"].get(nombre, True):
            return False, "herramienta=false"
        servicio = TOOLS[nombre][1] if nombre in TOOLS else None
        if servicio and not any(x["on"] for x in self.d["conexiones"][servicio]):
            return False, "conexion=false"
        return True, ""

    def visibles(self):
        """Herramientas que se le muestran al modelo: solo las encendidas (y con conexion activa)."""
        externas = [MCP_NOMBRE(c, h) for c in self.d["conexiones"]["mcp"] for h in c.get("herramientas", [])]
        return [n for n in [*TOOLS, *externas] if self.decidir(n)[0]]

    def credencial(self, servicio, banco, estricto=True):
        """Secreto de la primera conexion ON con valor; sin conexion ON falla (estricto) o usa la credencial principal."""
        cons = self.d["conexiones"].get(servicio, [])
        for con in [c for c in cons if c["on"]] + ([] if estricto else [c for c in cons if not c["on"]]):
            valor = banco.leer(LEGADO[servicio] if con["id"] == "defecto" else _clave_banco(servicio, con["id"])) if banco else None
            if valor:
                return valor
        raise RuntimeError(LEGADO.get(servicio, servicio) + " no disponible en banco")

    # --- acciones (UI del Director y herramientas del modelo) ---
    def _agent_access_lock(self, c, banco, actor):
        if "locked" in c:
            self.d["ia"] = not _booleano(c["locked"], "locked")
            self._sucio = True
        return {"ok": True, "sesion": str(c.get("sesion") or "web-general")[:60], "locked": not self.d["ia"]}

    def _tools_lock(self, c, banco, actor):
        cambio = {}
        if c.get("tool") is not None:
            nombre = c["tool"]
            if not (nombre in TOOLS or tipo(nombre) or self._mcp(str(nombre))):
                raise ValueError("herramienta desconocida")
            self.d["herramientas"][nombre] = not _booleano(c.get("locked"), "locked")
            cambio = {"tool": nombre, "locked": c["locked"]}  # el frontend lee {locked} del cambio
            self._sucio = True
        lista = [(n, TOOLS[n][0], True) for n in TOOLS] + [(n, "IA y agentes (delegacion)", True) for n in sorted(AGENTE_TOOLS | LLM_TOOLS)]
        lista += [(MCP_NOMBRE(k, h), "MCP · " + k["etiqueta"], False) for k in self.d["conexiones"]["mcp"] for h in k.get("herramientas", [])]
        h = self.d["herramientas"]
        tools = [{"nombre": n, "seccion": s, "locked": not h.get(n, defecto), "permitida": self.decidir(n, {"tools": True, "agente_tool": True, "llm_tool": True})[0]}
                 for n, s, defecto in lista]
        return {"tools": tools, "ia": self.d["ia"], **cambio}

    def _conexiones(self, c, banco, actor):
        servicio, cons = c.get("servicio"), self.d["conexiones"]
        if c.get("accion") in ("agregar", "activar") and servicio not in SERVICIOS:
            raise ValueError("servicio no soportado")
        if c.get("accion") == "agregar":
            if len(cons[servicio]) >= MAX_CONEXIONES:
                raise ValueError("maximo " + str(MAX_CONEXIONES) + " conexiones por servicio")
            nueva = {"id": uuid.uuid4().hex[:8], "etiqueta": _texto(c.get("etiqueta") or servicio, 60, "etiqueta"), "on": True}
            if servicio == "mcp":
                nueva.update(url=_texto(c.get("url"), 500, "url"), herramientas=[])
            if c.get("secreto") or servicio != "mcp":
                if not banco:
                    raise RuntimeError("banco no disponible")
                banco.guardar(_clave_banco(servicio, nueva["id"]), _texto(c.get("secreto"), 4096, "secreto"))
            cons[servicio].append(nueva)
            self._sucio = True
        elif c.get("accion") == "activar":
            con = next((x for x in cons[servicio] if x["id"] == c.get("id")), None)
            if not con:
                raise ValueError("conexion desconocida")
            con["on"] = _booleano(c.get("on"), "on")
            self._sucio = True
        elif c.get("accion") == "herramientas":  # lista descubierta de un servidor MCP externo
            con = next((x for x in cons["mcp"] if x["id"] == c.get("id")), None)
            if not con:
                raise ValueError("conexion desconocida")
            con["herramientas"] = [{"nombre": h["nombre"], "descripcion": str(h.get("descripcion") or "")[:300], "esquema": h.get("esquema") or {"type": "object"}}
                                   for h in c.get("lista", []) if MCP.fullmatch("mcp__00000000__" + str(h.get("nombre")))][:50]
            self._sucio = True
        return {"servicios": [{"servicio": s, "nombre": n, "conexiones": [{k: v for k, v in x.items() if k != "herramientas"} | {"herramientas": [h["nombre"] for h in x.get("herramientas", [])]}
                                                                          for x in cons[s]]} for s, n in SERVICIOS.items()]}

    def _checklist(self, c, banco, actor):
        lista, a = self.d["pendientes"], c.get("accion") or "listar"
        def buscar():
            x = next((x for x in lista if x["id"] == c.get("id")), None)
            if not x:
                raise ValueError("pendiente desconocido")
            return x
        if a == "agregar":
            if len(lista) >= MAX_PENDIENTES:
                raise ValueError("maximo " + str(MAX_PENDIENTES) + " pendientes")
            lista.append({"id": uuid.uuid4().hex[:8], "texto": _texto(c.get("texto"), 500, "texto"), "hecho": False})
        elif a == "marcar":
            x = buscar()
            x["hecho"] = _booleano(c["hecho"], "hecho") if "hecho" in c else not x["hecho"]
        elif a == "ordenar":
            ids = c.get("ids")
            if not isinstance(ids, list) or sorted(map(str, ids)) != sorted(x["id"] for x in lista):
                raise ValueError("ids debe contener todos los pendientes")
            lista.sort(key=lambda x: ids.index(x["id"]))
        elif a == "quitar":
            lista.remove(buscar())
        elif a != "listar":
            raise ValueError("accion de pendientes no soportada")
        self._sucio = self._sucio or a != "listar"
        return {"pendientes": [dict(x) for x in lista]}

    def _salas(self, c, banco, actor):
        salas, a = self.d["salas"], c.get("accion") or "listar"
        nivel = lambda s: 3 if actor == "director" else NIVELES.get(s["participantes"].get(actor), 0)  # noqa: E731
        def sala(minimo):
            s = salas.get(c.get("id"))
            if not s or nivel(s) < 1:
                raise ValueError("sala desconocida")
            if nivel(s) < minimo:
                raise PermissionError("acceso denegado a la sala: requiere " + {1: "lectura", 2: "escritura", 3: "admin"}[minimo])
            return s
        if a == "crear":
            if len(salas) >= MAX_SALAS:
                raise ValueError("maximo " + str(MAX_SALAS) + " salas")
            part = {actor: "admin"}
            for n, nv in (c.get("participantes") or {}).items():
                if nv not in NIVELES or not isinstance(n, str) or not n.strip() or len(n) > 40:
                    raise ValueError("participante invalido")
                part[n.strip()] = nv
            sid = uuid.uuid4().hex[:8]
            salas[sid] = {"id": sid, "nombre": _texto(c.get("nombre"), 80, "nombre"), "participantes": part, "contexto": "", "mensajes": [], "creada": time.time()}
        elif a == "enviar":
            s = sala(2)
            s["mensajes"].append({"de": str(c.get("de") or actor)[:40] if actor == "director" else actor, "texto": _texto(c.get("texto"), 4000, "texto"), "ts": time.time()})
            del s["mensajes"][:-MAX_MENSAJES]
        elif a == "contexto":
            sala(2)["contexto"] = _texto(c.get("texto"), 8000, "texto")
        elif a == "permiso":
            s = sala(3)
            n = _texto(c.get("participante"), 40, "participante")
            if c.get("nivel") is None:
                if n == "director":
                    raise PermissionError("no se puede quitar al director")
                s["participantes"].pop(n, None)
            elif c["nivel"] in NIVELES:
                s["participantes"][n] = c["nivel"]
            else:
                raise ValueError("nivel invalido")
        elif a == "borrar":
            if actor != "director":
                raise PermissionError("solo el director borra salas")
            sala(3)
            del salas[c["id"]]
        elif a == "leer":
            s = dict(sala(1))
            s["mensajes"] = s["mensajes"][-50:]
            return {"sala": s}
        elif a != "listar":
            raise ValueError("accion de salas no soportada")
        self._sucio = self._sucio or a != "listar"
        return {"salas": [{"id": s["id"], "nombre": s["nombre"], "participantes": s["participantes"], "mensajes": len(s["mensajes"])}
                          for s in salas.values() if nivel(s) >= 1]}

    def herramienta(self, nombre, args, actor="modelo"):
        return self.ejecutar({"pendientes": "checklist", "sala": "salas"}[nombre], args, None, actor)


ACCIONES = {"agent_access_lock", "tools_lock", "conexiones", "checklist", "salas"}


def MCP_NOMBRE(con, herramienta):
    return "mcp__" + con["id"] + "__" + herramienta["nombre"]


def _clave_banco(servicio, ident):
    return "CONN_" + servicio.upper() + "_" + ident
