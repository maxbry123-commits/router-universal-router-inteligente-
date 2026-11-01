"""Cliente Qwen compatible OpenAI. No guarda credenciales ni ejecuta tools."""
import json
import uuid
import os
import time
from urllib import error, request
from mvp import modelos

REINTENTABLES = {429, 502, 503, 504}
def _segundos(nombre, defecto):
    try:
        v = float(os.environ.get(nombre) or defecto)
        return v if v > 0 else float(defecto)
    except ValueError:
        return float(defecto)
QWEN_TIMEOUT_S = _segundos("RIU_QWEN_TIMEOUT_S", 180)  # solo la ruta no-SSE de Qwen; Groq/NVIDIA usan timeout_s() mas abajo
OPCIONES = {"tools", "tool_choice", "temperature", "top_p", "max_tokens",
            "parallel_tool_calls", "response_format", "enable_thinking", "reasoning_effort"}


def _endpoint(base_url):
    if not isinstance(base_url, str) or not base_url.startswith("https://"):
        if not (isinstance(base_url, str) and base_url.startswith("http://127.0.0.1:")):
            raise ValueError("QWEN_BASE_URL debe usar HTTPS o loopback de pruebas")
    return base_url.rstrip("/") + "/chat/completions"


def _solicitar(url, payload, clave):
    headers = {"Content-Type": "application/json", "User-Agent": "qwencloud-skills"}  # obligatorio en Token Plan (SDK oficial)
    if clave:
        headers["Authorization"] = "Bearer " + clave
    req = request.Request(url, data=json.dumps(payload).encode("utf-8"),
                          headers=headers, method="POST")
    with request.urlopen(req, timeout=QWEN_TIMEOUT_S) as resp:  # finito: un servidor que no contesta no cuelga el hilo para siempre (RIU_QWEN_TIMEOUT_S lo ajusta)
        return json.load(resp)


def llamar(mensajes, modelo, base_url, clave, opciones=None):
    """Devuelve texto, tool_calls, uso y respuesta cruda; reintenta solo fallos transitorios."""
    if not isinstance(mensajes, list) or not modelo:
        raise ValueError("Se requieren modelo y mensajes")
    payload = {"model": modelo, "messages": mensajes}  # igual que client.chat.completions.create del bloque (sin stream: el valor por defecto es no-stream)
    for nombre, valor in (opciones or {}).items():
        if nombre not in OPCIONES:
            raise ValueError("opcion Qwen no permitida: " + nombre)
        payload[nombre] = valor
    payload.update(modelos.extra_body(modelo, opciones=opciones))
    ultimo = RuntimeError("Qwen error de red")
    for base in modelos.bases(base_url):  # oficial primero, QwenCloud como alterna si la primera no acepta la clave o no responde
        try:
            return _intentar(_endpoint(base), payload, clave, modelo)
        except _Alterna as exc:
            ultimo = RuntimeError(str(exc))
    raise ultimo


class _Alterna(Exception):
    """Fallo de esa URL base (401/403/404 o red): vale la pena probar la otra."""


def _intentar(url, payload, clave, modelo):
    for intento in range(3):
        try:
            bruto = _solicitar(url, payload, clave)
            mensaje = bruto["choices"][0]["message"]
            return {"texto": mensaje.get("content") or "",
                    "tool_calls": mensaje.get("tool_calls") or [],
                    "finish_reason": bruto["choices"][0].get("finish_reason"),
                    "uso": bruto.get("usage") or {}, "bruto": bruto, "mensaje_asistente": mensaje,
                    "modelo_solicitado": modelo, "modelo_respuesta": bruto.get("model")}
        except error.HTTPError as exc:
            if exc.code == 400 and any(isinstance(m.get("content"), list) for m in payload["messages"]):
                payload = {**payload, "messages": [  # el modelo no admite imagen: se reintenta con solo el texto
                    ({**m, "content": "\n".join(p.get("text", "") for p in m["content"] if p.get("type") == "text") + "\n[imagenes adjuntas omitidas: este modelo no admite imagen]"}
                     if isinstance(m.get("content"), list) else m) for m in payload["messages"]]}
                continue
            if exc.code in (401, 403, 404):
                raise _Alterna("Qwen HTTP " + str(exc.code)) from None
            if exc.code not in REINTENTABLES or intento == 2:
                raise RuntimeError("Qwen HTTP " + str(exc.code)) from None
        except (error.URLError, TimeoutError, OSError):
            if intento == 2:
                raise _Alterna("Qwen error de red") from None
        time.sleep(min(2 ** intento, 2))


# --- Groq/NVIDIA (externos.py): lectura incremental SSE, timeout configurable y metricas. Qwen no pasa por aqui. ---
TIMEOUT_DEFECTO_S = 180.0

# ---- R8: TABLA UNICA DE TIMEOUTS (segundos). Regla: peticion al modelo < plazo del bridge (100 s, recorta cada peticion) y presupuesto TOTAL de reintentos == timeout del cliente del Harness. ----
# Misma tabla (mismos numeros) en chat-router/SWE CODE/web-bridge/src/respaldo.js (TIMEOUTS_DEFECTO, recortada por BRIDGE_DEADLINE_MS) y en
# router-mvp/fichas/fichas_qwen/fichas/politicas_modelo.json (politicas_externos[*].timeout_s); test_externos_a5.py y respaldo_a5.test.mjs verifican que no se contradigan.
TIMEOUTS_MODELO_S = {  # por peticion; en stream es de INACTIVIDAD entre fragmentos (no total)
    "groq/qwen/qwen3.8-27b": 60,                      # Groq: ~450 t/s y 16,384 tokens de salida maximo -> 36 s de generacion como mucho (console.groq.com/docs/models)
    "nvidia/minimaxai/minimax-m3.1-flash": 90,
    "nvidia/meta/muse-glimmer-30b": 180,
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b": 300,  # modelo de 550B con razonamiento: arranque lento
    "nvidia/z-ai/glm-5.3": 180,
}
PRESUPUESTO_TOTAL_S = 600.0  # = harness_client.TIMEOUT_LLM_S (RIU_HARNESS_TIMEOUT_S): suma de intentos + esperas de UNA llamada; un reintento que ya no cabe no empieza
TABLA_TIMEOUTS = (  # capa, donde se aplica, variable que lo cambia, segundos por defecto
    {"capa": "modelo", "donde": "externos.py / compute.timeout_s (Groq, NVIDIA)", "variable": "RIU_EXTERNOS_TIMEOUT_S o politicas_externos[modelo].timeout_s", "segundos": 180},
    {"capa": "modelo", "donde": "respaldo.js (bridge SWE CODE)", "variable": "RIU_SWE_TIMEOUTS / BRIDGE_RESPALDO_MS", "segundos": 90},
    {"capa": "bridge", "donde": "server.js conDeadline (tope de TODA la respuesta del bridge)", "variable": "BRIDGE_DEADLINE_MS", "segundos": 100},
    {"capa": "harness", "donde": "harness_client.py (llm / computar) y presupuesto de reintentos de externos.py", "variable": "RIU_HARNESS_TIMEOUT_S", "segundos": 600},
    {"capa": "harness", "donde": "harness_client.py swe_avanzar / swe_reanudar", "variable": "RIU_SWE_AVANZAR_TIMEOUT_MS", "segundos": 1800},
    {"capa": "proxy", "donde": "proxy HTTPS del Space/Vercel: mantiene viva la conexion con latidos SSE; no se confia en su limite", "variable": "(plataforma)", "segundos": 100},
)


def timeout_s(politica_s=None, defecto=TIMEOUT_DEFECTO_S):
    """Timeout en segundos: RIU_EXTERNOS_TIMEOUT_S manda; luego el de la politica del modelo; luego 180 s."""
    for valor in (os.environ.get("RIU_EXTERNOS_TIMEOUT_S"), politica_s):
        try:
            if valor not in (None, "") and float(valor) > 0:
                return float(valor)
        except (TypeError, ValueError):
            pass
    return float(defecto)


def nombre_de_trozos(trozos):
    """Nombre completo de una herramienta que el proveedor emite fragmentado. Tres formas reales: una sola vez; repetido entero en cada delta;
    acumulativo (git, github, github_leer) o en trozos disjuntos (github_ + leer). Solo se concatena en el ultimo caso."""
    if not trozos:
        return ""
    if len(set(trozos)) == 1:
        return trozos[0]  # repetido entero
    if all(b.startswith(a) for a, b in zip(trozos, trozos[1:])):
        return trozos[-1]  # cada delta contiene al anterior
    return "".join(trozos)


def argumentos_json_validos(texto):
    """True si los argumentos acumulados son un objeto JSON completo (vacio = sin argumentos)."""
    if not (texto or "").strip():
        return True
    try:
        return isinstance(json.loads(texto), dict)
    except ValueError:
        return False


class AcumuladorSSE:
    """Reconstruye una respuesta chat.completions a partir de sus lineas SSE (data: {...} / [DONE]).
    texto, razonamiento aparte, tool_calls por indice (id/name: ultimo valor no vacio; arguments: concatenados en orden),
    finish_reason, usage (tambien x_groq.usage) y metricas TTFT / tokens por segundo. Devuelve la misma forma que _intentar."""

    def __init__(self, al_texto=None, reloj=time.monotonic, herramientas=None):
        self._reloj, self._al_texto = reloj, al_texto
        self._declaradas = frozenset(n for n in (herramientas or ()) if isinstance(n, str) and n)  # nombres de tools declarados en la peticion (vacio: no se valida el nombre)
        self._t0, self._t1 = reloj(), None
        self.texto, self.razonamiento, self.finish_reason, self.uso, self.modelo = "", "", None, {}, None
        self._tools, self._orden, self._ultimo_id, self.invalidas, self.fragmentos = {}, [], None, 0, 0

    def _primer_dato(self):
        if self._t1 is None:
            self._t1 = self._reloj()

    def _tool(self, tc):
        i, f = tc.get("index"), tc.get("function") or {}
        if i is None:  # proveedor sin index: un id nuevo abre otra llamada; sin id continua la ultima
            i = tc.get("id") if tc.get("id") and tc.get("id") != self._ultimo_id else (self._orden[-1] if self._orden else 0)
        if i not in self._tools:
            self._tools[i] = {"id": "", "name": "", "arguments": "", "trozos": []}; self._orden.append(i)
        t = self._tools[i]
        if tc.get("id"):
            t["id"] = self._ultimo_id = tc["id"]
        if isinstance(f.get("name"), str) and f["name"]:
            t["trozos"].append(f["name"]); t["name"] = nombre_de_trozos(t["trozos"])  # R3: el nombre se RECONSTRUYE (github_ + leer = github_leer), nunca se reemplaza por el ultimo trozo
        t["arguments"] += f.get("arguments") or ""

    def linea(self, linea):
        """Procesa una linea SSE. True si era [DONE]. Lanza RuntimeError si el stream trae un error del proveedor."""
        if isinstance(linea, bytes):
            linea = linea.decode("utf-8", "replace")
        linea = linea.strip("\r\n")
        if not linea.startswith("data:"):
            return False  # lineas vacias, comentarios (: keep-alive), event:, id:, retry:
        dato = linea[5:].strip()
        if dato == "[DONE]":
            return True
        try:
            doc = json.loads(dato)
        except ValueError:
            self.invalidas += 1
            return False
        if not isinstance(doc, dict):
            return False
        if doc.get("error") and not doc.get("choices"):
            e = doc["error"] if isinstance(doc["error"], dict) else {"message": str(doc["error"])}
            codigo = e.get("code") if isinstance(e.get("code"), int) else None
            raise RuntimeError("stream " + ("HTTP %d" % codigo if codigo else "error") + ": " + str(e.get("message") or "")[:160])
        self.modelo = doc.get("model") or self.modelo
        uso = doc.get("usage") or (doc.get("x_groq") or {}).get("usage")
        if isinstance(uso, dict) and uso:
            self.uso = uso
        for opcion in doc.get("choices") or []:
            delta = opcion.get("delta") or {}
            r = delta.get("reasoning_content") or delta.get("reasoning")
            if r:
                self._primer_dato(); self.razonamiento += r; self.fragmentos += 1
            c = delta.get("content")
            if c:
                self._primer_dato(); self.texto += c; self.fragmentos += 1
                if self._al_texto:
                    self._al_texto(self.texto, c)
            for tc in delta.get("tool_calls") or []:
                self._primer_dato(); self._tool(tc); self.fragmentos += 1
            if opcion.get("finish_reason"):
                self.finish_reason = opcion["finish_reason"]
        return False

    def resultado(self, modelo_solicitado):
        fin = self._reloj()
        orden = sorted(self._orden) if all(isinstance(i, int) for i in self._orden) else self._orden
        # Algunos proveedores omiten el ID: sin él, el Harness no puede devolver el resultado al tool_call y la omite.
        # ID sintetico unico por llamada, solo cuando falte; conservar intacto el ID original si viene.
        # Normalizar argumentos vacios a un objeto JSON para compatibilidad OpenAI.
        llamadas = [{"id": self._tools[i]["id"] or "call_" + uuid.uuid4().hex[:24],
                     "type": "function",
                     "function": {"name": self._tools[i]["name"],
                                  "arguments": self._tools[i]["arguments"] or "{}"}} for i in orden]
        invalidas = []  # se MARCAN, no se descartan: ninguna llamada pendiente se pierde; quien las ejecute decide (no ejecutar incompletas)
        for ll in llamadas:
            if self._declaradas and ll["function"]["name"] not in self._declaradas:
                invalidas.append({"id": ll["id"], "nombre": ll["function"]["name"], "motivo": "nombre_no_declarado"})
            elif not argumentos_json_validos(ll["function"]["arguments"]):
                invalidas.append({"id": ll["id"], "nombre": ll["function"]["name"], "motivo": "argumentos_json_incompletos"})
        mensaje = {"role": "assistant", "content": self.texto or (None if llamadas else "")}
        if llamadas:
            mensaje["tool_calls"] = llamadas
        if self.razonamiento:
            mensaje["reasoning_content"] = self.razonamiento
        tokens = self.uso.get("completion_tokens") if isinstance(self.uso.get("completion_tokens"), int) else None
        estimados = tokens is None and self.fragmentos > 0
        origen = None if tokens is None and not estimados else "estimado" if estimados else "proveedor"
        tokens = self.fragmentos if estimados else tokens
        ttft = None if self._t1 is None else round(self._t1 - self._t0, 4)
        generando = None if self._t1 is None else fin - self._t1
        metricas = {"stream": True, "ttft_s": ttft, "duracion_s": round(fin - self._t0, 4), "tokens": tokens, "tokens_estimados": estimados, "origen_tokens": origen,
                    "tokens_por_s": round(tokens / generando, 2) if tokens and generando and generando > 0 else None, "lineas_invalidas": self.invalidas,
                    "tools_invalidas": len(invalidas)}
        bruto = {"object": "chat.completion", "model": self.modelo, "choices": [{"index": 0, "message": mensaje, "finish_reason": self.finish_reason}], "usage": self.uso}
        return {"texto": self.texto, "tool_calls": llamadas, "finish_reason": self.finish_reason, "uso": self.uso, "bruto": bruto,
                "mensaje_asistente": mensaje, "modelo_solicitado": modelo_solicitado, "modelo_respuesta": self.modelo, "metricas": metricas, "tools_invalidas": invalidas}
