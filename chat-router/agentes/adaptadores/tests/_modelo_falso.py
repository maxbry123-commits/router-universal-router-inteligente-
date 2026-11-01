"""Modelo FALSO local (solo para las pruebas de ejecucion REAL de los agentes: los agentes y CLIs son los reales, solo el LLM es de guion): OpenAI-compatible /v1/chat/completions (stream y no stream) y /v1/responses (Codex).
Guion: ESCRIBIR=<archivo>::<contenido> -> la primera vuelta pide la herramienta de escritura que el agente ofrezca; despues responde texto final."""
import json, sys, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def herramienta_escritura(tools):
    for t in tools or []:
        f = t.get("function") or t
        n = f.get("name", "")
        if n.lower() in ("write", "write_file", "file_editor", "str_replace_editor", "create_file", "writefile"):
            return n, f
    return None, None

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.endswith("/models"):
            return self._json(200, {"object": "list", "data": [{"id": "qwen2.5-coder-1.5b", "object": "model"}, {"id": "lfm2.5-350m", "object": "model"}]})
        self._json(404, {"error": "no"})
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); cuerpo = json.loads(self.rfile.read(n) or b"{}")
        self.server.visto.append({"path": self.path, "auth": self.headers.get("Authorization", ""), "body": cuerpo})
        ESCRIBIR = self.server.escribir
        if self.path.split("?")[0].endswith("/v1/messages"):
            texto = "TAREA_HECHA por modelo falso (anthropic)"
            if not cuerpo.get("stream"):
                return self._json(200, {"id": "msg_1", "type": "message", "role": "assistant", "model": cuerpo.get("model"), "content": [{"type": "text", "text": texto}], "stop_reason": "end_turn", "stop_sequence": None, "usage": {"input_tokens": 5, "output_tokens": 5}})
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
            def ev(t, d): self.wfile.write(("event: %s\ndata: %s\n\n" % (t, json.dumps({"type": t, **d}))).encode()); self.wfile.flush()
            ev("message_start", {"message": {"id": "msg_1", "type": "message", "role": "assistant", "model": cuerpo.get("model"), "content": [], "stop_reason": None, "usage": {"input_tokens": 5, "output_tokens": 1}}})
            ev("content_block_start", {"index": 0, "content_block": {"type": "text", "text": ""}})
            ev("content_block_delta", {"index": 0, "delta": {"type": "text_delta", "text": texto}})
            ev("content_block_stop", {"index": 0})
            ev("message_delta", {"delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 5}})
            ev("message_stop", {})
            return
        if self.path.endswith("/count_tokens"):
            return self._json(200, {"input_tokens": 5})
        if self.path.endswith("/chat/completions"):
            msgs = cuerpo.get("messages", [])
            hubo_tool = any(m.get("role") == "tool" for m in msgs)
            nombre, f = herramienta_escritura(cuerpo.get("tools"))
            call = None
            if ESCRIBIR and nombre and not hubo_tool:
                arch, cont = ESCRIBIR.split("::", 1)
                props = (f.get("parameters") or {}).get("properties", {})
                args = {}
                for k in props:
                    kl = k.lower()
                    if kl in ("filepath", "file_path", "path", "filename"): args[k] = arch
                    elif kl in ("content", "contents", "file_text", "text"): args[k] = cont
                    elif kl == "command": args[k] = "create"
                call = {"id": "call_1", "type": "function", "function": {"name": nombre, "arguments": json.dumps(args)}}
            texto = "" if call else "TAREA_HECHA por modelo falso"
            if cuerpo.get("stream"):
                self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
                def ev(d): self.wfile.write(("data: " + json.dumps(d) + "\n\n").encode()); self.wfile.flush()
                base = {"id": "c1", "object": "chat.completion.chunk", "created": 1, "model": cuerpo.get("model", "x")}
                if call:
                    ev({**base, "choices": [{"index": 0, "delta": {"role": "assistant", "tool_calls": [{"index": 0, **call}]}, "finish_reason": None}]})
                    ev({**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]})
                else:
                    ev({**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": texto}, "finish_reason": None}]})
                    ev({**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
                ev({**base, "choices": [], "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10}})
                self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush(); return
            msg = {"role": "assistant", "content": texto or None}
            if call: msg["tool_calls"] = [call]
            return self._json(200, {"id": "c1", "object": "chat.completion", "created": 1, "model": cuerpo.get("model", "x"),
                                    "choices": [{"index": 0, "message": msg, "finish_reason": "tool_calls" if call else "stop"}], "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10}})
        if self.path.endswith("/responses"):
            # API Responses (Codex): SSE con response.created / output_text / response.completed
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
            def ev(t, d): self.wfile.write(("event: %s\ndata: %s\n\n" % (t, json.dumps({"type": t, **d}))).encode()); self.wfile.flush()
            rid = "resp_1"
            ev("response.created", {"response": {"id": rid, "status": "in_progress", "model": cuerpo.get("model")}})
            ev("response.output_item.added", {"output_index": 0, "item": {"type": "message", "id": "msg_1", "role": "assistant", "content": [], "status": "in_progress"}})
            ev("response.output_text.delta", {"item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": "TAREA_HECHA por modelo falso"})
            ev("response.output_item.done", {"output_index": 0, "item": {"type": "message", "id": "msg_1", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "text": "TAREA_HECHA por modelo falso"}]}})
            ev("response.completed", {"response": {"id": rid, "status": "completed", "model": cuerpo.get("model"), "output": [{"type": "message", "id": "msg_1", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "text": "TAREA_HECHA por modelo falso"}]}], "usage": {"input_tokens": 5, "output_tokens": 5, "total_tokens": 10}}})
            return
        self._json(404, {"error": "ruta"})

def arrancar(escribir="", bind="127.0.0.1"):
    """-> servidor con .server_port y .visto (peticiones recibidas). escribir='ruta::contenido' hace que el modelo pida la herramienta de escritura del agente."""
    s = ThreadingHTTPServer((bind, 0), H)
    s.visto, s.escribir = [], escribir
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s
