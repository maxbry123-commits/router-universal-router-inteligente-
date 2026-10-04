# HANDOFF — FICHAS (para el agente que las va a crear y operar)

Actualizado: 2026-10-03 (Opus). Lee también `MANUAL-AGENTES.md` (misma carpeta) si es tu primera vez con el Router.

## Qué es una ficha (en simple)

- Una ficha es una **receta**: dice qué IA hace cada paso y en qué orden. Ejemplo: entrada → IA arquitectura → IA código → IA verifica → IA decide → salida.
- La ficha es **un archivo JSON**. El Router lo lee solo y lo convierte en una **sección nueva** con su propia dirección. **Nadie toca el Router.**
- Tú (el agente) **compones** la ficha: qué modelo va en cada paso, qué system prompt, qué instrucción. El Director decide la composición; tú la escribes, la pruebas y la dejas lista.

## Dónde vive

| Qué | Dónde |
|---|---|
| Fichas activas (las que el Router monta) | Almacenamiento HF `COMAND-CENTER-1/yaiwes-memoria-storage` → `router-inteligente-universal/fichas/<nombre>.json` |
| Plantilla vacía | Misma carpeta: `_plantilla.json` · por HTTP: `GET <puerta>/secciones/_plantilla` · en GitHub: `router inteligente universal/fichas/_plantilla.json` |
| Propuestas en GitHub (copia versionada) | `router inteligente universal/fichas/<nombre>.json` (rama `devin/1790824641-chat-agent-plan`) |
| Motor que las ejecuta | `router inteligente universal/integration/chat_mvp/secciones.py` (no lo toques) |

`<puerta>` = `https://comand-center-1-claude-github-mcp-backup.hf.space`

## Lo que necesitas

1. **Un token** `riu_...` con permiso `fichas` (y `chat`). Te lo da el Director. Va en `Authorization: Bearer <token>`.
2. Para **publicar** la ficha (que quede montada): la **clave del Director** en la cabecera `X-Director-Key`. Si el Director no te la dio para esta tarea, **no publicas**: dejas la ficha validada y probada en GitHub y avisas (paso 6).

## Paso a paso

**Orden con o sin clave del Director:** pasos 1 → 2 → 3 → 4 siempre. Con clave: 5 y luego 6. Sin clave: salta el 5 y haz el 6 (dejar la copia y avisar).
Antes de empezar: `GET <puerta>/secciones/<nombre>` te dice si ya existe una ficha con ese nombre (404 = no existe).

### Paso 1 — Copia la plantilla
```bash
curl -s -H "Authorization: Bearer $RIU_TOKEN" <puerta>/secciones/_plantilla > mi-ficha.json
```

### Paso 2 — Compón la ficha
Campos (todo en español, sin claves dentro):

| Campo | Qué poner |
|---|---|
| `nombre` | corto, minúsculas y guiones (`revision-codigo`). Será la dirección: `/secciones/revision-codigo/run` |
| `descripcion` | una frase |
| `modo` | `cadena` (cada paso recibe la salida del anterior), `paralelo` (todos reciben la misma entrada), `consejo` (todos + un `juez` que sintetiza), `unico` (solo el primer paso) |
| `anclaje_system_prompt` | reglas que valen para todos los pasos (opcional) |
| `pasos` | lista de 1 a 20 pasos, en orden. Cada paso: `nombre`, `modelo`, `system_prompt`, `instruccion`, `max_tokens`, `temperature` (opcional), `dataset` (opcional) |
| `juez` | solo en `consejo`: un paso más que junta las respuestas |
| `conectividad.tokens_permitidos` | quién puede usar la sección: `["*"]` todos, o patrones `["equipo-a/*"]` |
| `notas` | lo que el próximo agente debe saber |

- `modelo`: `auto` (cadena por defecto), un grupo (`assistants`, `code`...) o `proveedor:modelo` (`nvidia:moonshotai/kimi-k3`, `groq:qwen/qwen3.8-27b`). Lista viva: `GET <puerta>/fichas/catalog`.
- `instruccion`: el texto que recibe ese modelo. `{input}` se reemplaza por la entrada (o por la salida del paso anterior en `cadena`).
- `dataset`: `{"repo": "COMAND-CENTER-1/mi-dataset", "file": "anclaje.md"}` para sumar un texto de anclaje desde un dataset de HF.
- Usa `max_tokens` ≥ 400 en modelos que razonan (si no, pueden devolver respuesta vacía con `finish_reason: length`).
- **Entrada y salida no son pasos:** la entrada es el `input` que recibe la ficha y la salida es lo que devuelve el último paso (`final`). En `pasos` solo van las IA.
- **Cómo se arma el mensaje de cada paso:** system = `anclaje_system_prompt` + `system_prompt` del paso + texto del `dataset` (en ese orden); usuario = `instruccion` con `{input}` reemplazado.
- `temperature` y `dataset` son opcionales (pueden faltar o ir en `null`). El Router ignora `_ayuda` y `conectividad.nota`; puedes borrarlos.
- Si el Director no dio modelo ni `max_tokens` para cada paso, usa `auto` y los valores del ejemplo, y dilo al entregar.
- Tildes y eñes se permiten (el JSON es UTF-8).

Ejemplo de forma (la composición real la define el Director):
```json
{
  "nombre": "revision-codigo",
  "descripcion": "Del pedido a una decision revisada en 5 pasos",
  "modo": "cadena",
  "anclaje_system_prompt": "Responde en espanol. Se breve y concreto.",
  "pasos": [
    {"nombre": "arquitectura", "modelo": "auto", "system_prompt": "Eres arquitecto de software.", "instruccion": "Disena la solucion para: {input}", "max_tokens": 800},
    {"nombre": "codigo", "modelo": "code", "system_prompt": "Eres programador.", "instruccion": "Escribe el codigo de este diseno: {input}", "max_tokens": 1500},
    {"nombre": "verifica", "modelo": "auto", "system_prompt": "Eres revisor estricto.", "instruccion": "Busca errores en: {input}", "max_tokens": 800},
    {"nombre": "decide", "modelo": "auto", "system_prompt": "Eres el jefe tecnico.", "instruccion": "Decide si se aprueba y que falta: {input}", "max_tokens": 500}
  ],
  "juez": null,
  "conectividad": {"tokens_permitidos": ["*"], "vias": ["http", "mcp"]},
  "notas": ""
}
```

### Paso 3 — Valida (sin clave del Director)
```bash
curl -s -X POST -H "Authorization: Bearer $RIU_TOKEN" -H "Content-Type: application/json" \
  -d "{\"ficha\": $(cat mi-ficha.json)}" <puerta>/secciones/validar
```
Respuesta `{"valida": true, ...}` o `{"valida": false, "error": "..."}`. Corrige hasta que diga `true`.

### Paso 4 — Prueba con una entrada real (sin clave del Director, sin publicar)
```bash
curl -s -X POST -H "Authorization: Bearer $RIU_TOKEN" -H "Content-Type: application/json" \
  -d "{\"ficha\": $(cat mi-ficha.json), \"input\": \"texto de prueba\"}" <puerta>/secciones/probar
```
Devuelve `final` (la salida) y `steps` (qué hizo cada paso: `paso`, `model`, `ok`, `ms`, `content`). Si un paso sale `ok: false` (con `auto` o un grupo, el Router ya probó los modelos de respaldo de esa cadena), cambia el `modelo` de ese paso o sube `max_tokens`. Ajusta y repite hasta que el resultado sea el esperado. Una prueba de 4 pasos puede tardar 1–3 minutos.

### Paso 5 — Publica (solo con la clave del Director)
```bash
curl -s -X POST -H "Authorization: Bearer $RIU_TOKEN" -H "X-Director-Key: $DIRECTOR_KEY" -H "Content-Type: application/json" \
  -d "{\"ficha\": $(cat mi-ficha.json)}" <puerta>/secciones
```
En ≤ 60 s queda montada como sección (o al instante con `POST /secciones/recargar`). Comprueba:
```bash
curl -s -H "Authorization: Bearer $RIU_TOKEN" <puerta>/secciones      # debe aparecer con "estado": "ok"
```

### Paso 6 — Guarda la copia en GitHub y avisa
- Guarda el mismo JSON en `router inteligente universal/fichas/<nombre>.json` de la rama `devin/1790824641-chat-agent-plan`, con tu propio acceso a GitHub (el que te dio el Director para este repo; no es el token `riu_`). Commit: `Ficha <nombre>: <qué hace>`.
- Si no tienes acceso a GitHub, entrega el JSON completo al Director en tu respuesta.
- Si **no** tenías la clave del Director: deja el archivo en GitHub, valida (paso 3) y prueba (paso 4), y avisa al Director: "ficha `<nombre>` lista para publicar". Él la publica con una sola llamada (paso 5).

## Cómo se usa una ficha publicada

| Forma | Cómo |
|---|---|
| HTTP directo | `POST <puerta>/secciones/<nombre>/run` con `{"input": "..."}` |
| MCP | herramienta `seccion_run` (`nombre`, `input`); lista con `secciones_listar` |
| SDK | `Router("riu_...").seccion("<nombre>", "entrada")` |
| Sin cablear nada | el Director amarra un token a la ficha (`POST /tokens/ficha/<token>` `{"ficha": "<nombre>"}`): todo lo que ese token mande al chat normal (`/v1/router/chat/completions`) pasa por la ficha |

## Cambiar o quitar una ficha

- **Cambiar:** edita el JSON, valida, prueba y vuelve a publicar con el mismo `nombre` (reemplaza). Guarda la versión en GitHub.
- **Quitar:** `DELETE <puerta>/secciones/<nombre>` con `X-Director-Key`.
- **Espejo / versión nueva sin perder la anterior:** publica con otro `nombre` (`revision-codigo-v2`).

## Cómo saber si algo falla

- `GET <puerta>/secciones`: cada sección dice `estado: ok` o `estado: error` con el motivo.
- Ventana status en HF: `router-inteligente-universal/Ventana status router inteligente universal/secciones.json`.
- Errores típicos: `SIN_PASOS`, `MODO_DESCONOCIDO`, `403 TOKEN_NO_PERMITIDO_EN_ESTA_SECCION` (revisa `tokens_permitidos`), `403 CLAVE_DIRECTOR_REQUERIDA` (estás publicando sin la clave).

## Lo que NO haces

- No editas `secciones.py` ni ningún archivo del Router.
- No pones claves ni tokens dentro de la ficha.
- No publicas sin la clave del Director ni la pides a otro agente.
- No borras fichas de otros.
