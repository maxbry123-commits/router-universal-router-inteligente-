"""Passwordless chat entry. Infrastructure credentials remain server-side in the vault."""
import os
from integration.chat_mvp.app import app

class ChatAccess:
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if scope["type"]=="http":
            path=scope.get("path","")
            public=(path.startswith("/plugins/puente_chat/call/")
                    or path.startswith("/plugins/fichas/call/")
                    or path.startswith("/plugins/fichas_qwen/call/")
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
