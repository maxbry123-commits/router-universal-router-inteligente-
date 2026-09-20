# Chat MVP — arquitectura (RIU-0105, 2026-09-20)

Documento adjunto a esta carpeta; su contenido debe fusionarse al README de arquitectura cuando se parta en tramos
(no se reescribió el README grande para no arriesgar historial).

```
NAVEGADOR /chat (chat_ui.html)                     AGENTES (50+) con su key MAXBRY-NNN
   │  X-API-Key (Router) · X-Provider-Key / X-GitHub-Token (BYOK opcional)
   ▼
FastAPI  integration/chat_mvp/app.py
   ├─ /chat/send ──► build mensajes (agente + documentos + historial) ──► caché?
   │        └─► route_chat_completion  (FastAPI → Enchufe Gate → RedUniversal)
   │                └─► executor de proveedor: providers.chat(hf | cerebras | nvidia | groq | local)
   ├─ /chat/agents · /chat/documents · /chat/conversations · /chat/graph · /chat/storage(/sync)
   └─ /chat/github/{accounts,whoami,repos,file,commit}   (cuenta = etiqueta → variable de entorno, o token por petición)

Almacenamiento (RIU_DATA_DIR=/data, montado desde el bucket HF en el Space)
   sql        SQLite: conversaciones, mensajes, agentes
   graph      nodos/aristas de procedencia con valid_at (owner→conversación→modelo/agente/documento/repo)
   cache      respuestas con TTL y contador de aciertos
   documents  archivos por sha256 + metadatos; ventana de documentos en la UI
```

## Reglas vigentes
- Cada turno pasa por el hot-path certificado; el chat no llama a proveedores fuera del Router.
- Modelos HF no certificados (Kimi K3, DeepSeek V4, MiniMax) solo se intentan con `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` y se devuelven `certified=false`.
- Ningún `model_id` se inventa: salen del registry, del catálogo vivo del router HF o del catálogo del proveedor.
- Claves nunca en el repo: secrets del entorno o BYOK por petición; no se guardan ni se devuelven.

## Estado
Ejecutado en runner (ver `Claude notas/RIU-0105-registro-chat-mvp.md`). Despliegue en Hugging Face bloqueado por falta de `HF_WRITE_TOKEN`.
Fuera de alcance de este nodo (Paso 3 del Director): router por grupos 0/1/2 con salto Nvidia/Cerebras → local → DeepSeek V4 Flash, límites de RAM, biblioteca de skills HF.
