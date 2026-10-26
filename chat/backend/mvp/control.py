"""Permisos y estado del chat decididos en el servidor; el frontend solo los muestra.
Tres permisos separados: conexion ON, herramienta ON y delegacion IA ON (solo para herramientas que llaman IA/agentes).
El estado (sin secretos) se persiste por /almacen; los secretos de las conexiones viven en el banco cifrado."""
import base64
import hashlib
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
         "almacen": ("Hugging Face", "hf"), "pendientes": ("Chat", None), "sala": ("Chat", None),
         "agente": ("IA y agentes", None), "llm": ("IA y agentes", None), "yaiwes_md": ("Chat", None)}  # delegar en un agente / en otro modelo
NIVELES = {"lectura": 1, "escritura": 2, "admin": 3}
MCP = re.compile(r"mcp__([0-9a-f]{8})__([A-Za-z0-9_-]{1,49})")
MAX_CONEXIONES, MAX_PENDIENTES, MAX_SALAS, MAX_MENSAJES = 10, 200, 20, 500
MAX_ARCHIVO, MAX_PROYECTOS, MAX_AGENTES = 700_000, 50, 50  # bytes de un archivo subido (hf_store admite 1 MB ya en base64)


def tipo(nombre):
    return "agente_tool" if nombre in AGENTE_TOOLS else "llm_tool" if nombre in LLM_TOOLS else None


def _vacio():
    base = {s: [] for s in SERVICIOS}
    for s in LEGADO:
        base[s].append({"id": "defecto", "etiqueta": "Principal (banco)", "on": True})
    return {"ia": False, "herramientas": {}, "conexiones": base, "pendientes": [], "salas": {}, "archivos": {}, "sandbox": {}, "handoff": {}, "proyectos": {}, "agentes_on": False, "agentes": {}, "prompt_on": False}


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
        t = tipo(nombre)
        if t:  # delegacion: el servidor manda (ia para otros modelos, agentes_on para agentes); si llegan flags del cliente tambien deben estar en true
            if controles is not None and not (controles.get("tools") and controles.get(t)):
                return False, ("tools" if not controles.get("tools") else t) + "=false"
            if not self.d["agentes_on" if t == "agente_tool" else "ia"]:
                return False, ("agentes" if t == "agente_tool" else "ia") + "=false"
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
        if "locked" in c:  # quien: ia (otros modelos), agentes, o todo (por defecto)
            quien, on = c.get("quien", "todo"), not _booleano(c["locked"], "locked")
            if quien not in ("ia", "agentes", "todo", "prompt"):
                raise ValueError("quien debe ser ia, agentes, todo o prompt")
            if quien == "prompt":  # system prompt completo (core + bloques) como capa externa; apagado = chat normal
                self.d["prompt_on"] = on
            elif quien != "agentes":
                self.d["ia"] = on
            if quien in ("agentes", "todo"):
                self.d["agentes_on"] = on
            self._sucio = True
        return {"ok": True, "sesion": str(c.get("sesion") or "web-general")[:60], "locked": not (self.d["ia"] or self.d["agentes_on"]),
                "ia_locked": not self.d["ia"], "agentes_locked": not self.d["agentes_on"], "prompt_locked": not self.d["prompt_on"]}

    def _tools_lock(self, c, banco, actor):
        cambio = {}
        if c.get("tool") is not None:
            nombre = c["tool"]
            if not (nombre in TOOLS or tipo(nombre) or self._mcp(str(nombre))):
                raise ValueError("herramienta desconocida")
            self.d["herramientas"][nombre] = not _booleano(c.get("locked"), "locked")
            cambio = {"tool": nombre, "locked": c["locked"]}  # el frontend lee {locked} del cambio
            self._sucio = True
        lista = [(n, TOOLS[n][0], True) for n in TOOLS]
        lista += [(MCP_NOMBRE(k, h), "MCP · " + k["etiqueta"], False) for k in self.d["conexiones"]["mcp"] for h in k.get("herramientas", [])]
        h = self.d["herramientas"]
        tools = [{"nombre": n, "seccion": s, "locked": not h.get(n, defecto), "permitida": self.decidir(n, {"tools": True, "agente_tool": True, "llm_tool": True})[0]}
                 for n, s, defecto in lista]
        return {"tools": tools, "ia": self.d["ia"], "agentes_on": self.d["agentes_on"], **cambio}

    # --- agentes conectables: cada uno = nombre + modelo + instrucciones; el chat o el modelo los llaman como una sesion nueva ---
    def _poner_agente(self, nombre, recurso, sistema):
        from mvp import modelos
        if not re.fullmatch(r"[\w .-]{1,40}", str(nombre or "").strip()):
            raise ValueError("nombre de agente invalido (1 a 40 letras, numeros, espacio, punto o guion)")
        if recurso not in {i for i, t in modelos.catalogo() if t == "texto"}:
            raise ValueError("recurso desconocido: elige un modelo de texto del plan")
        n = nombre.strip()
        if n not in self.d["agentes"] and len(self.d["agentes"]) >= MAX_AGENTES:
            raise ValueError("maximo %d agentes" % MAX_AGENTES)
        if not isinstance(sistema, str) or len(sistema) > 4000:
            raise ValueError("instrucciones: texto de hasta 4000 caracteres")
        self.d["agentes"][n] = {"recurso": recurso, "sistema": sistema}
        self._sucio = True

    def _tools_estado(self, c, banco, actor):
        from mvp import modelos
        return {"agentes": [{"nombre": n, "recurso": a["recurso"], "modelo": a["recurso"], "sistema": a.get("sistema", "")} for n, a in self.d["agentes"].items()],
                "recursos": [{"id": i, "nombre": i, "grupo": "Qwen Token Plan", "via": "Router", "rol": ""} for i, t in modelos.catalogo() if t == "texto"],
                "fichas": [], "tools": list(TOOLS), "claves": {}, "max": MAX_AGENTES}

    def _agente_enlazar(self, c, banco, actor):
        previo = self.d["agentes"].get(str(c.get("nombre") or "").strip(), {})
        self._poner_agente(c.get("nombre"), c.get("recurso"), c["sistema"] if "sistema" in c else previo.get("sistema", ""))
        return self._tools_estado(c, banco, actor)

    def _groq_agentes(self, c, banco, actor):  # el panel guarda la lista completa (p. ej. al quitar un agente)
        lista = c.get("agentes")
        if not isinstance(lista, list) or len(lista) > MAX_AGENTES:
            raise ValueError("agentes debe ser una lista de hasta %d" % MAX_AGENTES)
        self.d["agentes"] = {}
        for a in lista:
            a = a if isinstance(a, dict) else {}
            self._poner_agente(a.get("nombre"), a.get("recurso") or a.get("modelo"), a.get("sistema") or "")
        self._sucio = True
        return self._tools_estado(c, banco, actor)

    def _conexiones(self, c, banco, actor):
        servicio, cons = c.get("servicio"), self.d["conexiones"]
        if c.get("accion") in ("agregar", "activar", "quitar") and servicio not in SERVICIOS:
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
        elif c.get("accion") == "quitar":  # libera el hueco (tope por servicio) y vacía su secreto en el banco
            if c.get("id") == "defecto" or not any(x["id"] == c.get("id") for x in cons[servicio]):
                raise ValueError("conexion desconocida o principal (no se quita)")
            cons[servicio] = [x for x in cons[servicio] if x["id"] != c.get("id")]
            if banco and banco.leer(_clave_banco(servicio, c["id"])) is not None:
                banco.guardar(_clave_banco(servicio, c["id"]), "")
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

    # --- espacio de trabajo del chat: estado, archivos subidos, sandbox y proyectos (lo que ya pedía el frontend) ---
    def _status(self, c, banco, actor):
        return {"ok": True, "servicio": "router_mvp", "ia": self.d["ia"]}

    def _estado(self, c, banco, actor):
        return {"sesion": str(c.get("sesion") or "web-general")[:60], "ia": self.d["ia"], "pendientes": len(self.d["pendientes"]), "salas": len(self.d["salas"]),
                "archivos": sum(len(v) for v in self.d["archivos"].values()), "conexiones_on": {s: sum(1 for x in v if x["on"]) for s, v in self.d["conexiones"].items()}}

    def _herramientas_estado(self, c, banco, actor):
        return self._tools_lock({}, banco, actor)

    def validar_subida(self, c):
        nombre = c.get("nombre")
        if not isinstance(nombre, str) or not 1 <= len(nombre) <= 120 or "/" in nombre or "\\" in nombre or nombre.startswith("."):
            raise ValueError("nombre de archivo invalido")
        try:
            datos = base64.b64decode(c.get("datos_b64") or "", validate=True)
        except (ValueError, TypeError):
            raise ValueError("datos_b64 invalido") from None
        if not datos or len(datos) > MAX_ARCHIVO:
            raise ValueError("el archivo debe pesar entre 1 byte y %d KB" % (MAX_ARCHIVO // 1000))
        return ruta_archivo(c, nombre), len(datos)

    def _subir(self, c, banco, actor):
        ruta, tam = self.validar_subida(c)
        self.d["archivos"].setdefault(clave_espacio(c), {})[c["nombre"]] = {"tam": tam, "tipo": str(c.get("tipo") or "texto")[:80], "ts": time.time(), "ruta": ruta}
        self._sucio = True
        return {"ok": True, "nombre": c["nombre"], "tam": tam}

    def _archivos(self, c, banco, actor):
        return {"archivos": [n for n, m in self.d["archivos"].get(clave_espacio(c), {}).items() if not m.get("borrado")]}

    def _archivo_borrar(self, c, banco, actor):
        meta = self.d["archivos"].get(clave_espacio(c), {}).get(c.get("nombre"))
        if not meta:
            raise ValueError("archivo desconocido")
        meta["borrado"] = not c.get("restaurar")  # borrado lógico: el contenido sigue en el almacén hasta que se sobrescriba
        self._sucio = True
        return {"ok": True, "nombre": c["nombre"], "borrado": meta["borrado"]}

    def ruta_de(self, nombre, sesion):
        """Ruta en el almacén de un archivo subido por esa sesión (cualquier carpeta), para anclarlo al contexto."""
        for clave, idx in self.d["archivos"].items():
            meta = idx.get(nombre)
            if meta and not meta.get("borrado") and (clave.endswith("|" + str(sesion)) or clave.startswith("constitucion|")):
                return meta["ruta"]
        return None

    def _texto_sesion(self, c, clave):
        ses = str(c.get("sesion") or "web-general")[:60]
        if "texto" in c:
            texto = c["texto"]
            if not isinstance(texto, str) or len(texto) > 20000:
                raise ValueError("texto debe ser cadena de hasta 20000 caracteres")
            if texto.strip():
                self.d[clave][ses] = texto
            else:
                self.d[clave].pop(ses, None)
            self._sucio = True
        return self.d[clave].get(ses, "")

    def _sandbox(self, c, banco, actor):
        texto = self._texto_sesion(c, "sandbox")
        return {"sandbox": texto, "encendido": bool(texto)}

    def _handoff_texto(self, c, banco, actor):  # yaiwes.md: informacion del proyecto que pegan el Director o el modelo; global y viaja con cada mensaje
        if c.get("accion") == "leer":
            c = {k: v for k, v in c.items() if k != "texto"}
        texto = self._texto_sesion({**c, "sesion": "yaiwes"}, "handoff")
        return {"texto": texto, "encendido": bool(texto)}

    def _proyecto(self, c, banco, actor):
        ps, op = self.d["proyectos"], c.get("op") or "list"
        pid = str(c.get("project_id") or "")[:60]
        if op in ("upsert", "get", "delete", "link_chat", "unlink_chat") and not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", pid):
            raise ValueError("project_id invalido")
        if op == "upsert":
            if pid not in ps and len(ps) >= MAX_PROYECTOS:
                raise ValueError("maximo %d proyectos" % MAX_PROYECTOS)
            p = ps.setdefault(pid, {"project_id": pid, "nombre": pid, "chats": [], "created_at": time.time()})
            for k in ("nombre", "notas", "estado"):
                if k in c:
                    p[k] = str(c[k])[:2000]
            if "encendido" in c:
                p["encendido"] = bool(c["encendido"])
            for k in ("anclas", "items"):
                if isinstance(c.get(k), list):
                    p[k] = [str(x)[:500] for x in c[k]][:200]
            p["updated_at"] = time.time()
            self._sucio = True
            return {"ok": True, "proyecto": p}
        if op in ("link_chat", "unlink_chat"):
            p = ps.get(pid)
            if not p:
                raise ValueError("proyecto desconocido")
            ses = str(c.get("sesion") or "")[:60]
            p["chats"] = [x for x in p["chats"] if x != ses] + ([ses] if op == "link_chat" and ses else [])
            self._sucio = True
            return {"ok": True, "proyecto": p}
        if op == "delete":
            ps.pop(pid, None)
            self._sucio = True
            return {"ok": True}
        if op == "get":
            if pid not in ps:
                raise ValueError("proyecto desconocido")
            return {"ok": True, "proyecto": ps[pid]}
        if op == "list":
            return {"proyectos": list(ps.values())}
        raise ValueError("op de proyecto no soportada")

    def herramienta(self, nombre, args, actor="modelo"):
        return self.ejecutar({"pendientes": "checklist", "sala": "salas", "yaiwes_md": "handoff_texto"}[nombre], args, None, actor)


ACCIONES = {"agent_access_lock", "tools_lock", "conexiones", "checklist", "salas", "status", "estado", "herramientas_estado",
            "archivos", "subir", "archivo_borrar", "sandbox", "handoff_texto", "proyecto", "tools_estado", "agente_enlazar", "groq_agentes"}


def clave_espacio(c):
    """Carpeta lógica de un archivo: destino (chat/constitucion/proyecto) + proyecto + sesión."""
    return "|".join((str(c.get("destino") or "chat"), str(c.get("project_id") or ""), str(c.get("sesion") or "web-general")))[:160]


def ruta_archivo(c, nombre):
    return "chat_archivos/" + hashlib.sha1(clave_espacio(c).encode()).hexdigest()[:12] + "/" + nombre


def MCP_NOMBRE(con, herramienta):
    return "mcp__" + con["id"] + "__" + herramienta["nombre"]


def _clave_banco(servicio, ident):
    return "CONN_" + servicio.upper() + "_" + ident
