# ➡️📂 Motor de búsqueda

Motor de búsqueda web multi-proveedor para Router Inteligente Universal.

## Objetivo

Ejecutar búsqueda fuera del chat usando Hugging Face Jobs ON_DEMAND y escribir el resultado en archivos para que Claude/Sol/agentes lean solo el resultado final.

Flujo:

TRIGGER -> Hugging Face Job -> 5 proveedores -> deduplicación/ranking determinista -> result.json + summary.md

No usa GitHub Actions. No usa LLM por defecto.

## Proveedores

1. ddgs — metasearch sin API key; combina varios motores disponibles.
2. brave — BRAVE_SEARCH_API_KEY.
3. tavily — TAVILY_API_KEY.
4. serper — SERPER_API_KEY.
5. firecrawl — FIRECRAWL_API_KEY.

El scraper HTML directo de DuckDuckGo se conserva solo como fallback interno opcional; no es el proveedor principal porque HF puede recibir challenge/CAPTCHA.

Los proveedores sin secreto quedan GAP; el motor continúa con los disponibles.

## Archivos

- websearch_engine.py — ejecuta, agrega, deduplica, puntúa y escribe resultados.
- trigger_hf_websearch.py — dispara Hugging Face Job directamente con run_job().
- test_websearch_engine.py — tests deterministas sin red.

## Salida

Durante el Job, por defecto:

/tmp/websearch-results/<JOB_ID>/result.json

/tmp/websearch-results/<JOB_ID>/summary.md

Para persistencia hay dos rutas:

1. GitHub directo (sin GitHub Actions): si el entorno que activa el trigger tiene GITHUB_TOKEN, el Job publica summary.md en:
   router inteligente universal/websearch-results/<JOB_ID>/summary.md
   y realiza read-back antes de declarar publicación verificada.

2. Storage Bucket HF opcional: pasar --volume con formato:
   hf://buckets/<owner>/<bucket>:/data
   y usar /data/websearch/results como output.

summary.md es la vista compacta que debe leer el agente para reducir contexto/tokens.

## Uso local

python websearch_engine.py "consulta"

## Trigger HF directo

python trigger_hf_websearch.py "consulta"

Opcional:

python trigger_hf_websearch.py "consulta" --providers ddgs,brave,tavily,serper,firecrawl --worker HF1

Conserva el patrón del centro de cómputo existente:
- namespace: COMAND-CENTER-1
- flavor: cpu-upgrade
- workers lógicos: HF1, HF2, HF3
- lifecycle: ON_DEMAND
- engine pinneado a commit probado
- sin GitHub Actions

Persistencia por GitHub:
python trigger_hf_websearch.py "consulta" --publish-github auto

Persistencia por bucket, cuando la credencial tenga permiso:
python trigger_hf_websearch.py "consulta" --volume hf://buckets/COMAND-CENTER-1/yaiwes-v54:/data

## Secretos

Nunca se imprimen claves. Solo se reenvían al Job mediante secrets= cuando ya existen en el entorno que activa el trigger. Esto aplica a las claves de búsqueda y a GITHUB_TOKEN.

## PASS

VERIFIED_CLOSED exige:
1. consulta válida;
2. al menos un resultado;
3. result.json escrito;
4. summary.md escrito;
5. read-back de result.json coherente.

Si un proveedor falla, queda registrado como GAP sin ocultarse.
