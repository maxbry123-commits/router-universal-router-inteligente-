"""Middleware runtime Salida 2. Preserva tool_calls/reasoning/citations intactos."""
import json, time, os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse

CHAT_SUFFIX = "/v1/chat/completions"
TOKENS_PER_CHAR = float(os.environ.get("TOKENS_PER_CHAR", "0.25"))
COST_PER_TOKEN = float(os.environ.get("COST_PER_TOKEN_USD", "0.000001"))

def _count_tokens(text):
    return max(1, int(len(text or "") * TOKENS_PER_CHAR))

class ChatRuntimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not (request.method == "POST" and request.url.path.endswith(CHAT_SUFFIX)):
            return await call_next(request)
        t0 = time.time()

        try:
            from ext_endpoints import task_store, queue_bridge
        except Exception as e:
            print(f"[runtime] ext_endpoints ausente: {e}")
            return await call_next(request)

        if getattr(queue_bridge, "_closed", False):
            body = json.dumps({"error": {
                "code": "QUEUE_CLOSED",
                "message": "cola cerrada, POST /v1/queue/reopen",
                "recovery": "abrir cola"}}).encode()
            return Response(content=body, status_code=503,
                            media_type="application/json",
                            headers={"x-request-id": getattr(request.state, "request_id", "")})

        raw = await request.body()
        req_data = {}
        try: req_data = json.loads(raw or b"{}") or {}
        except Exception: pass
        wants_stream = bool(req_data.get("stream"))

        # ADAPTACION DECLARADA (ficha 017): el task se creaba SIN payload, asi que
        # /v1/chat/search y /v1/chat/export.md no tenian NINGUN mensaje que leer
        # (el store ya soporta payload; solo faltaba guardarlo).
        task = task_store.create(kind="chat", status="sending",
                                  payload={"messages": req_data.get("messages") or []})
        tid = task["task_id"]
        try:
            response = await call_next(request)
        except Exception as e:
            task_store.update(tid, status="error",
                error={"code":"INTERNAL","message":str(e)})
            raise

        buf = b""
        async for c in response.body_iterator: buf += c

        status_label = "done" if response.status_code < 400 else "error"
        task_store.update(tid, status=status_label,
            progress={"step":1,"total":1,"label":status_label})

        headers = dict(response.headers)
        headers["x-task-id"] = tid
        headers["x-ttft-ms"] = str(int((time.time()-t0)*1000))

        if wants_stream and response.status_code == 200:
            try:
                data = json.loads(buf)
                content = data["choices"][0]["message"]["content"]
            except Exception:
                content = buf.decode("utf-8","replace")
            async def gen():
                for i in range(0, len(content), 32):
                    yield "data: " + json.dumps({"choices":[{"delta":{"content":content[i:i+32]}}]}) + "\n\n"
                yield "data: [DONE]\n\n"
            headers.pop("content-length", None)
            # ADAPTACION DECLARADA: el content-type original (application/json)
            # viajaba en headers y Starlette NO lo sobreescribe con media_type
            # si ya esta presente -> la respuesta SSE salia como application/json.
            headers.pop("content-type", None)
            headers["cache-control"] = "no-cache"
            headers["x-accel-buffering"] = "no"
            return StreamingResponse(gen(), media_type="text/event-stream",
                                     headers=headers)

        # Enriquecer usage/cost sin borrar tool_calls/reasoning/citations
        try:
            data = json.loads(buf)
            if isinstance(data, dict):
                if "choices" in data and "usage" not in data:
                    txt = ""
                    for c in data.get("choices", []):
                        txt += (c.get("message", {}) or {}).get("content") or ""
                    ct = _count_tokens(txt)
                    data["usage"] = {"prompt_tokens": 0,
                                     "completion_tokens": ct,
                                     "total_tokens": ct,
                                     "cost_estimate_usd": round(ct * COST_PER_TOKEN, 6)}
                if not data.get("model"): data["model"] = "deterministic"
                if "created" not in data: data["created"] = int(time.time())
                buf = json.dumps(data).encode()
        except Exception: pass

        headers["content-length"] = str(len(buf))
        return Response(content=buf, status_code=response.status_code,
                        headers=headers, media_type="application/json")
