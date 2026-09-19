# SECCION 14 (pendiente de fusionar en Claude notas/memoria.md)

NOTA OPERATIVA: este contenido deberia vivir como Seccion 14 al final de
`Claude notas/memoria.md` (que a esta fecha termina en la Seccion 13,
websearch component). Se crea como archivo separado porque un outage
temporal del clasificador de seguridad de Bash/Agent en esta sesion
impidio leer+concatenar el archivo de 54KB de forma segura antes de que
se cerrara la ventana de contexto. PRIMERA TAREA del siguiente Claude:
leer `Claude notas/memoria.md` completo, pegar este contenido al final
como Seccion 14 (sin borrar nada existente), y luego borrar este archivo
separado (`Claude notas/HANDOFF-2026-09-19-seccion14.md`) para no dejar
duplicados permanentes.

---

## 14. HANDOFF DE VENTANA (2026-09-19) — PARA EL SIGUIENTE CLAUDE SONNET

Contexto de Anthropic al 96%. El Director sigue en la misma sesion/plan de
trabajo cuando se reabra la ventana. Este bloque es el estado real,
verificable, para retomar sin repetir preguntas ya resueltas.

### 14.0 Reglas de autorizacion en vigor (no volver a preguntar)
- P1 "SI": autorizado a iniciar.
- P2: autorizado a reparar sobre la marcha, sin escalar, resolviendo GAPs
  dentro del alcance. "100 autorizado."
- P3 (dura, sigue vigente): SOLO crear/escribir en el repo
  `router-universal-router-inteligente-` (owner `maxbry123-commits`).
  NUNCA en `agentes` ni otro repo del ecosistema, aunque el PAT tenga
  acceso admin a todos.
- P4: replicar el metodo de trabajo de `agentes/Claude notas/`.
- Autorizacion amplia del Director (verbatim, sigue en pie): "Tienes mi
  autorizacion total completa para gestionar en cualquier momento
  cualquier accion en mis cuentas."
- LIMITE QUE EL CLAUDE ACTUAL IMPUSO Y DEBE MANTENERSE pese a la
  autorizacion amplia: nunca escribir credenciales de terceros
  (HF/GitHub/Groq/NVIDIA/Cerebras) en texto plano dentro del repo ni
  repetirlas en el chat. Motivo: ya fueron expuestas en texto plano en
  el chat por el Director en esta sesion (ver 14.4). Esto no es
  negociable por "autorizacion total" — es un limite de higiene de
  secretos, no de permiso.

### 14.1 PRIORIDAD 1 — Chat MVP HF (estado: funcional, pendiente credenciales reales)
- Archivo: `router inteligente universal/gateway/hf_chat_mvp/app.py`
  (SHA actual `9a7c1d81d5e4f134725274fa4f770078d744103d`, commit `a2e3d8c`).
  Gradio + selector proveedor/modelo. Proveedores: Hugging Face
  (`router.huggingface.co/v1`, env `HF_TOKEN_1`), Groq, NVIDIA NIM,
  Cerebras. Modelos HF ya corregidos: incluye
  `moonshotai/Kimi-K3` (verificado oficial, no K2.5), `deepseek-ai/DeepSeek-V4.1-Flash`,
  `deepseek-ai/DeepSeek-V4-Pro`.
- `requirements.txt` y `README.md` (instrucciones de deploy) ya están en
  el mismo folder, pusheados.
- PENDIENTE: el Director debe crear el HF Space el mismo
  ("New Space" -> SDK Gradio -> "Sync with a GitHub repo" ->
  `maxbry123-commits/router-universal-router-inteligente-`, carpeta
  `router inteligente universal/gateway/hf_chat_mvp/`) y cargar los
  secrets del Space (`HF_TOKEN_1`, `GROQ_API_KEY_1`, `NVIDIA_API_KEY_1`,
  `CEREBRAS_API_KEY_1`) el mismo desde Settings -> Variables and
  secrets. Claude no tiene conector a HF, no puede hacerlo por el.

### 14.2 PRIORIDAD 2 — Auditoria de modelos locales/HF (parcial)
Verificado en esta sesion via WebSearch/WebFetch (fuentes oficiales):
- **DeepSeek-V4 es REAL y oficial** (`api-docs.deepseek.com/news/news260424/`,
  2026-04-24). DeepSeek-V4-Pro (1.6T/49B activos) y DeepSeek-V4-Flash
  (284B/13B activos), 1M contexto. `deepseek-ai/DeepSeek-V4.1-Flash` en
  HF confirma org verificada `deepseek-ai`, MIT, Inference Providers
  activo (Novita +2). CORRECCION IMPORTANTE: una conclusion anterior en
  este mismo documento (si existe una Seccion 12 previa diciendo que
  DeepSeek-V4 era "namespace squatting") ES INCORRECTA y queda anulada
  por este hallazgo — DeepSeek-V4 SI es oficial.
- **Kimi K3 es REAL y oficial**: `huggingface.co/moonshotai/Kimi-K3`,
  org verificada `moonshotai`, servido via Together AI + 2 proveedores
  mas via HF Inference Providers, disponible en HuggingChat, licencia
  propia "Kimi K3 License" (no MIT).
- **PENDIENTE / NO VERIFICADO todavia**: MiniMax M3 (el Director pide
  "Mínimax me"/"MiniMax M3" en varias prioridades — no se confirmo aun
  si existe como tal en HF o si el nombre correcto es MiniMax-M2 /
  M2.7, que SI aparece ya en `app.py` bajo NVIDIA NIM como
  `minimaxai/minimax-m2.7`). Falta: buscar "MiniMax M3" oficial en HF +
  fuente oficial MiniMax antes de dar por buena esa referencia.
- **PENDIENTE**: "otros AI de code disponibles" que el Director pidio
  evaluar (ademas de Kimi K3 / MiniMax / DeepSeek V4 / GLM 5) — no se
  investigo en esta sesion.
- Fuente cruzada: `Readme arquitectura router inteligente universal/README.md`
  ya tiene una tabla "REMOTE20 V2" (nodo RIU-0094, de una sesion previa)
  con 20 model_ids incl. 4 variantes DeepSeek-V4, todos
  "PROVIDER_LIVE_VERIFIED" pero 0/20 "REMOTE_INFERENCE_AUTHENTICATED_PASS"
  por `GAP_AUTH_REMOTE_INFERENCE` (falta credencial valida en las
  pruebas) — GAP de autenticacion, no de existencia del modelo.

### 14.3 PRIORIDAD 3 — Modulos por token (Kimi K3, MiniMax, DeepSeek V4) conectados a GitHub + HF
Diseño acordado, no completado:
- Los tres modelos (mas GLM 5 para code) se acceden **todos con el mismo
  `HF_TOKEN_1`** via `router.huggingface.co/v1` (HF Inference Providers)
  — no requieren cuentas/API keys separadas por proveedor. Esto es lo
  que el Director pidio explicitamente ("para mi es mejor porque
  centralizado todo sin abrir cuentas en cada proveedor") y ya esta
  reflejado en `app.py`.
- "Conectados a mis repos de GitHub/HF": la conexion real GitHub<->HF es
  la que se hace al crear el HF Space con "Sync with a GitHub repo"
  (14.1) — no existe una via oficial confirmada para que un chat de
  DeepSeek/HuggingChat escriba directamente en GitHub por MCP mas alla
  de eso; se investigo (HF MCP server oficial en
  `huggingface.co/docs/hub/hf-mcp-server`, HuggingChat MCP Tools en
  `huggingface.co/docs/chat-ui/configuration/mcp-tools`) y son reales,
  pero conectar "DeepSeek chat + MCP + este repo de GitHub" en un flujo
  automatico de 0 friccion NO tiene soporte oficial documentado — es
  tarea manual del Director via el HF Space + GitHub sync.
- PENDIENTE no resuelto: la referida "Tarea 1 / Tarea 2" de un plan de
  HF hecho por "sol gpt" — buscado en el repo (code search "TAREA-1
  OR TAREA-2"), 0 resultados. Puede estar en otro repo del ecosistema
  (fuera del alcance P3) o con otro nombre de archivo. Sigue sin
  localizar.

### 14.4 PRIORIDAD 4 — API keys y "aceleradores" para que el otro grupo de Claude continue
- **100 API keys del Router YA GENERADAS** con el `APIKeyManager`
  certificado existente (sin modificarlo):
  `router inteligente universal/security/api_key_manager.py`
  (SHA `cd5d6735a7f90f6168895c794257c2895927fd38`, sin cambios).
  - `agent_id` = `MAXBRY-001` .. `MAXBRY-100`, formato de key
    `riu_MAXBRY-NNN_<random>`, scope `route`, sin restriccion de modelo.
  - Hashes (PBKDF2-HMAC-SHA256, 200k iter, salt por key) persistidos en
    `router inteligente universal/security/keystore/maxbry_100_api_keys_hash_state.json`
    (commit `6871117`, SHA `810e87862b9832b4a1c0af04f7961b3091f5d178`).
  - **Texto plano entregado UNA SOLA VEZ al Director via SendUserFile**
    (CSV `maxbry_100_api_keys_PLAINTEXT.csv`), NUNCA comiteado a git.
    Si el Director necesita repartir esas 100 keys al "otro grupo de
    Claude", debe hacerlo el mismo desde ese CSV — Claude no las tiene
    mas (no se persisten en ningun lado accesible a Claude).
  - **MAX_SLOTS=100 QUEDA LLENO.** Cualquier alta nueva de key requiere
    `revoke()` de un slot existente primero (fail-closed por diseno).
- **Credenciales de proveedores externos (HF, GitHub, Groq, NVIDIA,
  Cerebras) pegadas en texto plano en el chat por el Director en esta
  sesion**: NO fueron escritas a ningun archivo del repo ni a GitHub
  Secrets por Claude. Estado real verificado via API de GitHub: solo
  existen como GitHub Secrets reales `CEREBRAS_API_KEY_1..6` y
  `RIU_GITHUB_PAT_FULL_ACCESO` (7 secrets, de antes de esta sesion). NO
  existe secret de HF en GitHub todavia (el Director cree que si existe
  uno, no es asi segun la API).
  - RECOMENDACION QUE SIGUE PENDIENTE DE QUE EL DIRECTOR EJECUTE:
    1. Rotar TODAS las credenciales pegadas en el chat (especialmente
       los PATs de GitHub "full access" — equivalen a contraseñas de
       cuenta).
    2. Crear los nuevos secrets el mismo, directamente en GitHub UI
       (Settings -> Secrets and variables -> Actions -> New repository
       secret): `HF_TOKEN_1`, `GROQ_API_KEY_1`, `NVIDIA_API_KEY_1`
       (los de Cerebras ya existen).
    3. Una vez creados, el workflow
       `.github/workflows/riu-validate-provider-keys.yml` (ya en el
       repo, commit `ba31100`, id de workflow `361855231`) los valida
       contra los endpoints reales de cada proveedor sin que Claude
       vea los valores — correrlo manualmente desde la pestaña Actions
       (el dispatch via API dio 422 varias veces, probable delay de
       indexado de GitHub; no confirmado si ya se resolvio).
- Esto es lo que el "otro grupo de Claude" necesita para operar: las
  100 keys del Router (ya generadas, entregadas al Director) + que el
  Director complete el paso 2-3 de arriba para las claves de
  proveedores reales.

### 14.5 PRIORIDAD 5 — Plan de integracion del Router (pendiente, no arrancado en esta sesion)
Este segmento completo (2026-09-19) fue un desvio hacia el tema
DeepSeek/HF-chat/API-keys por instruccion directa del Director. **Las
auditorias forenses pase 3 y 4 de 4** (el mandato original, cubriendo
`router inteligente software/`, `Documentos proyectos router
inteligente universal/`, `dataset Yaiwes/`, `Yaiwes Cognitive Control
Plane/` y el resto del pool de 64 componentes donantes) siguen SIN
EMPEZAR. Tampoco se sincronizaron `STATE.json` / `PLAN-TAREAS.md` /
`CHECKPOINT.json` en esta sesion. Esto deberia ser lo primero que
retome el siguiente Claude una vez resueltas las prioridades 1-4 de
arriba, salvo que el Director indique otra cosa.

### 14.6 PRIORIDAD 6 — Contexto e instrucciones 1 a 1
Todo el detalle linea-por-linea de mensajes del Director en este
segmento (DeepSeek/HF/API keys) esta documentado en el resumen de
sesion que genera Anthropic al cortar por limite de contexto — pedirle
al Director el enlace/resumen de la sesion previa si hace falta el
detalle verbatim; este documento (`memoria.md`) es el registro
persistente resumido y operativo, no pretende sustituir el transcript
completo.

### 14.7 Archivos tocados en esta sesion (referencia rapida de SHAs)
- `router inteligente universal/gateway/hf_chat_mvp/app.py` ->
  `9a7c1d81d5e4f134725274fa4f770078d744103d` (commit `a2e3d8c`)
- `router inteligente universal/gateway/hf_chat_mvp/requirements.txt` ->
  `9a9844eb482e5f7f70076ea1eea6525045ec0f60` (sin cambios en esta sesion)
- `router inteligente universal/gateway/hf_chat_mvp/README.md` ->
  `c18e679d1a19302c847773f80ac241f239e31075` (sin cambios en esta sesion)
- `.github/workflows/riu-validate-provider-keys.yml` ->
  `72df8815302773b9530dec6d0d88659d12d99ca1` (commit `ba31100`, sin
  confirmar dispatch exitoso todavia)
- `router inteligente universal/security/api_key_manager.py` ->
  `cd5d6735a7f90f6168895c794257c2895927fd38` (SIN MODIFICAR, solo leido
  y usado)
- `router inteligente universal/security/keystore/maxbry_100_api_keys_hash_state.json`
  (NUEVO) -> `810e87862b9832b4a1c0af04f7961b3091f5d178` (commit `6871117`)
- Este archivo (`Claude notas/HANDOFF-2026-09-19-seccion14.md`) -> ver
  commit de este push. PENDIENTE fusionarlo dentro de
  `Claude notas/memoria.md` como Seccion 14 y luego borrarlo.
