# T-06 — Cadena Rowboat → Ruflo → Claude Code → Grok → Claude Code → 4 Meta
**Estado:** PENDIENTE · **Depende de:** T-04 y T-05 · **Nodo:** N-06 · **Paso P2**

## Qué es, en palabras simples
Una cadena de trabajo donde cada eslabón le pasa el resultado al siguiente, con el plugin DeepSeek Harness (`ruflo-deepseek-harness`) como pieza central. Todo pasa por el Router único.

## Eslabones (orden dado por el Director)
1. Rowboat 2. Ruflo 3. Claude Code 4. Grok 5. Claude Code 6. los 4 Meta.
"Grok es parte de lo que vas a hacer": Grok es un eslabón más y también se conecta por el Router.

## Cómo se hace
1. Cada eslabón se describe como una tarea en esquema DSL DAG (determinista, no texto libre).
2. Cada uno llama al Router con `RouterCliente` (no se abre otra puerta).
3. Claude Code usa la pasarela (`chat router/09-CLAUDE-CODE/pasarela.py`).
4. Hermes y OpenClaw corren en paralelo como sentinelas.
5. Se usa la cola durable de Fables (`SQLiteDurableStore`) y el enchufe universal de Fables (carpeta de coda workflow persistencias).
6. Un espejo y una plantilla por tarea; mostrar los 4–5 chats descargados.

## Listo cuando
Una corrida completa de punta a punta deja evidencia por eslabón y ninguna llamada sale fuera del Router.

## No hacer
Escribir código desde cero: se poda, se edita quirúrgico y se cablea lo ya descargado. Usar APIs de Anthropic.
