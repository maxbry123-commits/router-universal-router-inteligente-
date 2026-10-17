"""Passwordless chat entry. Infrastructure credentials remain server-side in the vault."""
import os, time, json
from collections import deque
from integration.chat_mvp.app import app

# rate-limit suave por IP: solo envios de chat (chat_async/chat/send); el polling /resultado no cuenta.
# 120 envios / 10 min por IP: holgado para pruebas manuales intensas, corta solo abusos.
_RL_N = int(os.getenv("RIU_RL_ENVIOS", "120")); _RL_S = 600
_RL: dict = {}
_HILOS = [False]


def _ip(scope):
    for k, v in scope.get("headers", []):
        if k.lower() == b"x-forwarded-for":
            return v.decode(errors="ignore").split(",")[0].strip()
    c = scope.get("client") or ("", 0)
    return str(c[0])


def _limitado(scope) -> bool:
    path = scope.get("path", "")
    if scope.get("method") != "POST" or not (path.endswith("/chat_async") or path.endswith("/call/chat") or path == "/chat/send"):
        return False
    now = time.time(); q = _RL.setdefault(_ip(scope), deque())
    while q and now - q[0] > _RL_S: q.popleft()
    if len(q) >= _RL_N: return True
    q.append(now)
    if len(_RL) > 5000:
        for k in [k for k, v in _RL.items() if not v][:2000]: _RL.pop(k, None)
    return False

class ChatAccess:
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if scope["type"]=="http":
            if not _HILOS[0]:  # /resultado y el resto son def sincronos: mas hilos para que el long-poll no bloquee (anyio por defecto 40)
                _HILOS[0]=True
                try:
                    import anyio.to_thread
                    anyio.to_thread.current_default_thread_limiter().total_tokens=100
                except Exception:
                    pass
            if _limitado(scope):
                body=json.dumps({"status":"error","reason":"RATE_LIMIT","detail":"Demasiados envios seguidos; espera un momento"}).encode()
                await send({"type":"http.response.start","status":429,"headers":[(b"content-type",b"application/json"),(b"retry-after",b"30")]})
                await send({"type":"http.response.body","body":body})
                return
            path=scope.get("path","")
            public=(path.startswith("/plugins/puente_chat/call/")
                    or path.startswith("/plugins/fichas/call/")
                    or path.startswith("/plugins/fichas_qwen/call/")
                    or path.startswith("/plugins/secretos/call/")
                    or path.startswith("/plugins/watchdog/call/")
                    or path.startswith("/memoria/")
                    or path.startswith("/espacio/")
                    or path.startswith("/chat/")
                    or (path=="/plugins" and scope.get("method")=="GET"))
            key=os.getenv("RIU_PUBLIC_CHAT_KEY")
            if public and key:
                scope=dict(scope)
                scope["headers"]=[(k,v) for k,v in scope.get("headers",[]) if k.lower()!=b"x-api-key"]+[(b"x-api-key",key.encode())]
        await self.app(scope,receive,send)
app.add_middleware(ChatAccess)
