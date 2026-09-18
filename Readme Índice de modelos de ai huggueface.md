# Readme Índice de modelos de AI Hugging Face — inventario corregido

## Regla de verdad
`ROUTER_REGISTERED != ACCOUNT_INSTALLED` y `CATALOG_OBSERVED != TESTED != READY`.

La certificación histórica de 20 slots del Router **no es un inventario de modelos instalados en la cuenta Hugging Face**. El usuario corrigió esa interpretación el 2026-09-17.

## Registro activo provisional del Router
Estos 7 IDs permanecen únicamente como referencias activas del Router hasta una verificación autenticada de instalación/uso. **No se declaran instalados en COMAND-CENTER-1.**
- `Qwen/Qwen3-0.6B` — PROVIDER_AUTH_FLAGGED
- `openai-community/gpt2` — INTEGRATION_VERIFIED_STORAGE_RW_AUTH_FLAGGED
- `Qwen/Qwen3-8B` — COMPUTE_VERIFIED_NOT_READY
- `Qwen/Qwen2.5-7B-Instruct` — CATALOG_OBSERVED
- `Qwen/Qwen2.5-1.5B-Instruct` — CATALOG_OBSERVED
- `farbodtavakkoli/OTel-2.0-LLM-31B-IT` — CATALOG_OBSERVED
- `openai/gpt-oss-20b` — CATALOG_OBSERVED

## Modelos retirados del registro activo por corrección del usuario
- `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`
- `facebook/opt-125m`
- `Qwen/Qwen2.5-0.5B-Instruct`
- `Qwen/Qwen3-4B`
- `Qwen/Qwen2.5-3B-Instruct`
- `openai/gpt-oss-120b`
- `Qwen/Qwen3-32B`
- `dphn/dolphin-2.9.1-yi-1.5-34b`
- `deepseek-ai/DeepSeek-V4-Flash-0731`
- `ornith-ai/Ornith-1.0-9B-GGUF`
- `ornith-ai/Ornith-1.5-9B-GGUF`
- `Qwen/Qwen-72B`
- `Qwen/Qwen2.5-7B-Instruct-AWQ`

Motivo común: aparecían en catálogo/Jobs históricos, pero esa evidencia no demuestra que sean modelos instalados o propios de la cuenta.

## Inventario real de cuenta
Estado: `GAP_PENDING_FRESH_AUTHENTICATED_INVENTORY`.
La conexión actual confirma identidad `COMAND-CENTER-1`, pero el endpoint directo de búsqueda de modelos no está disponible. No se inferirá “0 modelos” ni se reutilizará el catálogo histórico como sustituto.

## Siguiente gate
Obtener evidencia autenticada de repos/modelos privados/propios y de cualquier almacenamiento/cache persistente usado por el Router; deduplicar contra Jobs; sólo entonces recalcular cómputo y mirrors.


## Inventario real verificable — RIU-0085
- Cuenta autenticada: `COMAND-CENTER-1`.
- Repos de modelos **propiedad de la cuenta** obtenidos con consulta autenticada: **0**. Evidencia HF Job `6aacb9175c02253cfb1461d1`.
- Mirrors de repos materializados y verificados: **0**. RIU-0078 documentó diseño, no ejecución.
- Instalaciones locales persistentes verificadas: **0**.
- Modelos con **inferencia real verificada en HF Jobs**:
  - `Qwen/Qwen3-0.6B`
  - `openai-community/gpt2`
  - `Qwen/Qwen3-8B`
- Referencias activas del Router sin prueba suficiente de instalación persistente:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `Qwen/Qwen2.5-1.5B-Instruct`
  - `farbodtavakkoli/OTel-2.0-LLM-31B-IT`
  - `openai/gpt-oss-20b`

### Video / Animation Models — solicitados, no instalados aún
- `Wan-AI/Wan2.2-Animate-14B` — task video-to-video, Diffusers, ~17.27B params, licencia HF=`apache-2.0`, estado=`GAP_PENDING`.
- `Lightricks/LTX-Video` — image-to-video, Diffusers, ~1.923B params, licencia HF=`other`; términos exactos pendientes, estado=`GAP_PENDING`.
- `tencent/HunyuanVideo` — text-to-video, licencia HF=`other`; términos exactos pendientes, estado=`GAP_PENDING`.

Regla: `REGISTERED/GAP_PENDING != DOWNLOADED != HASH_VERIFIED != LOAD_TESTED != PASS`.
