# Proxy minimo :7860 -> router :7861 / web-bridge :7870 / puente-movil :7862 / openclaw :18789
import json, os, httpx, asyncio
import websockets
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import Response, StreamingResponse, JSONResponse, FileResponse, RedirectResponse
from starlette.websockets import WebSocketState
ROUTER = "http://127.0.0.1:%s" % os.environ.get("ROUTER_PORT", "7861")
BRIDGE = "http://127.0.0.1:%s" % os.environ.get("BRIDGE_PORT", "7870")
PUENTE = "http://127.0.0.1:%s" % os.environ.get("PUENTE_PORT", "7862")
PUENTE_WS = "ws://127.0.0.1:%s" % os.environ.get("PUENTE_PORT", "7862")
OPENCLAW = "127.0.0.1:%s" % os.environ.get("OPENCLAW_PORT", "18789")

_OC_DROP_PREFIXES = ("x-forwarded-", "x-real-", "cf-", "true-client-", "x-original-")
_OC_DROP = {"host", "content-length", "transfer-encoding", "connection", "content-encoding",
            "forwarded", "via", "x-forwarded-for", "x-forwarded-proto", "x-forwarded-host",
            "x-forwarded-port", "x-real-ip"}
def openclaw_hdrs(req_headers):
    # Strip HF ingress proxy headers, rebuild safe chain for OpenClaw trustedProxies.
    out = {}
    for k, v in req_headers.items():
        lk = k.lower()
        if lk in _OC_DROP or any(lk.startswith(pref) for pref in _OC_DROP_PREFIXES):
            continue
        out[k] = v
    out["X-Forwarded-For"] = "203.0.113.10"
    out["X-Forwarded-Proto"] = "https"
    out["X-Forwarded-Host"] = "comand-center-1-riu-router.hf.space"
    out["Host"] = "127.0.0.1:%s" % os.environ.get("OPENCLAW_PORT", "18789")
    return out

app = FastAPI()
cli = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
HOP = {"host", "content-length", "transfer-encoding", "connection", "content-encoding"}

async def fwd(base, path, req, body):
    hdrs = {k: v for k, v in req.headers.items() if k.lower() not in HOP}
    r = cli.build_request(req.method, base + path, params=req.query_params, headers=hdrs, content=body)
    resp = await cli.send(r, stream=True)
    oh = {k: v for k, v in resp.headers.items() if k.lower() not in (HOP - {"content-encoding"})}
    # Nunca devolver Location absoluto a 127.0.0.1 (rompe el host público HF)
    for k, v in list(oh.items()):
        if k.lower() == "location" and ("127.0.0.1" in v or "localhost" in v):
            from urllib.parse import urlparse
            u = urlparse(v)
            oh[k] = (u.path or "/") + (("?" + u.query) if u.query else "")
    async def it():
        try:
            async for c in resp.aiter_raw():
                yield c
        finally:
            await resp.aclose()
    return StreamingResponse(it(), status_code=resp.status_code, headers=oh)

def is_web(model):
    return isinstance(model, str) and (
        model.startswith(("web-", "swecode-", "groq/", "nvidia/"))
        or model in {"lfm2.5-350m", "qwen2.5-coder-1.5b", "qwen3.5-0.8b", "qwen3-0.6b"})

@app.api_route("/web", methods=["GET", "HEAD"])
async def web_noslash(req: Request):
    # Evitar caer al catch-all del router (307 Absolute a 127.0.0.1:7861/web/)
    q = ("?" + req.url.query) if req.url.query else ""
    return RedirectResponse(url="/web/" + q, status_code=307)

@app.api_route("/web/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def web_root(req: Request):
    # Bridge Express no define GET / → 404 Cannot GET /; mapear a /health
    return await fwd(BRIDGE, "/health", req, await req.body())

@app.api_route("/web/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def web(path: str, req: Request):
    if not path:
        return await fwd(BRIDGE, "/health", req, await req.body())
    return await fwd(BRIDGE, "/" + path, req, await req.body())

@app.get("/v1/queue")
async def queue(req: Request):
    return await fwd(BRIDGE, "/v1/queue", req, b"")

@app.get("/v1/models")
async def models(req: Request):
    data = []
    for base in (ROUTER, BRIDGE):
        try:
            r = await cli.get(base + "/v1/models", headers={k: v for k, v in req.headers.items() if k.lower() == "authorization"}, timeout=15)
            if r.status_code == 200:
                data += r.json().get("data", [])
        except Exception:
            pass
    return JSONResponse({"object": "list", "data": data})

APK_PATH = os.environ.get("APK_PATH", "/data/apk/swecode-agente.apk")

@app.api_route("/apk", methods=["GET", "HEAD"])
async def apk():
    if not os.path.isfile(APK_PATH):
        try:
            from huggingface_hub import hf_hub_download
            import shutil
            os.makedirs(os.path.dirname(APK_PATH), exist_ok=True)
            shutil.copy(hf_hub_download("COMAND-CENTER-1/swe-code-hf-gguf", "apk/swecode-agente.apk", repo_type="dataset", token=os.environ.get("HF_TOKEN")), APK_PATH)
        except Exception as e:
            return JSONResponse({"error": "apk no disponible: %s" % type(e).__name__}, status_code=404)
    return FileResponse(APK_PATH, media_type="application/vnd.android.package-archive", filename="swecode-agente.apk")

@app.api_route("/movil/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD"])
async def movil(path: str, req: Request):
    return await fwd(PUENTE, "/" + path, req, await req.body())

@app.get("/movil")
async def movil_root(req: Request):
    return await fwd(PUENTE, "/health", req, b"")

@app.websocket("/agente")
async def agente_ws(ws: WebSocket):
    await ws.accept(subprotocol=ws.headers.get("sec-websocket-protocol"))
    proto = ws.headers.get("sec-websocket-protocol")
    extra = {}
    if proto:
        extra["subprotocols"] = [proto]
    try:
        async with websockets.connect(PUENTE_WS + "/agente", extra_headers={}, **extra) as up:
            async def c2u():
                try:
                    while True:
                        msg = await ws.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        if "text" in msg and msg["text"] is not None:
                            await up.send(msg["text"])
                        elif "bytes" in msg and msg["bytes"] is not None:
                            await up.send(msg["bytes"])
                except Exception:
                    pass
            async def u2c():
                try:
                    async for m in up:
                        if isinstance(m, bytes):
                            await ws.send_bytes(m)
                        else:
                            await ws.send_text(m)
                except Exception:
                    pass
            await asyncio.wait([asyncio.create_task(c2u()), asyncio.create_task(u2c())], return_when=asyncio.FIRST_COMPLETED)
    except Exception:
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.close()

# --- OpenClaw Gateway: HTTP + WebSocket bajo /openclaw/ ---
@app.websocket("/openclaw")
@app.websocket("/openclaw/{path:path}")
async def openclaw_ws(ws: WebSocket, path: str = ""):
    sub = ws.headers.get("sec-websocket-protocol")
    protos = [p.strip() for p in sub.split(",")] if sub else None
    qs = ("?" + ws.url.query) if ws.url.query else ""
    hdrs = openclaw_hdrs(ws.headers)
    # keep only auth/ua for WS upstream (no forwarded)
    hdrs = {k: v for k, v in hdrs.items() if k.lower() in ("authorization", "user-agent", "cookie")}
    try:
        up = await websockets.connect("ws://%s/%s%s" % (OPENCLAW, path, qs), subprotocols=protos,
                                      additional_headers=hdrs, max_size=None, open_timeout=10)
    except TypeError:
        try:
            up = await websockets.connect("ws://%s/%s%s" % (OPENCLAW, path, qs), subprotocols=protos,
                                          extra_headers=hdrs, max_size=None, open_timeout=10)
        except Exception:
            await ws.close(code=1011); return
    except Exception:
        await ws.close(code=1011); return
    await ws.accept(subprotocol=up.subprotocol)
    async def c2u():
        while True:
            m = await ws.receive()
            if m["type"] == "websocket.disconnect": break
            await up.send(m["bytes"] if m.get("bytes") is not None else m["text"])
    async def u2c():
        async for m in up:
            await (ws.send_bytes(m) if isinstance(m, bytes) else ws.send_text(m))
    t = [asyncio.create_task(c2u()), asyncio.create_task(u2c())]
    await asyncio.wait(t, return_when=asyncio.FIRST_COMPLETED)
    for x in t: x.cancel()
    await up.close()
    try: await ws.close()
    except Exception: pass

@app.api_route("/openclaw", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@app.api_route("/openclaw/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def openclaw_http(req: Request, path: str = ""):
    body = await req.body()
    hdrs = openclaw_hdrs(req.headers)
    url = "http://%s/openclaw/%s" % (OPENCLAW, path)
    r = cli.build_request(req.method, url, params=req.query_params, headers=hdrs, content=body)
    resp = await cli.send(r, stream=True)
    oh = {k: v for k, v in resp.headers.items() if k.lower() not in (HOP - {"content-encoding"})}
    async def it():
        try:
            async for c in resp.aiter_raw():
                yield c
        finally:
            await resp.aclose()
    return StreamingResponse(it(), status_code=resp.status_code, headers=oh)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def rest(path: str, req: Request):
    body = await req.body()
    if path.startswith("v1/") and body:
        try:
            if is_web(json.loads(body).get("model")):
                return await fwd(BRIDGE, "/" + path, req, body)
        except Exception:
            pass
    return await fwd(ROUTER, "/" + path, req, body)
