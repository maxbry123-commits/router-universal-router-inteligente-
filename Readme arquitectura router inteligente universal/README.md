# Arquitectura router inteligente universal

Repositorio: `maxbry123-commits/router-universal-router-inteligente-`
Rama: `main`
Contrato operativo: `tel.workflow/v3`
Modo: `FAIL_CLOSED_LOOP`

## Alcance autorizado — 3 pasos
1. Integrar componentes open source disponibles en la raíz del Router y auditar LLM/Hugging Face para adapters/FastAPI por modelo confirmado.
2. Cablear, podar duplicación y escribir solo código faltante; capa/filtro LLM únicamente cuando exista contrato definido/recuperado.
3. Ejecutar tests reales Hugging Face + GitHub + API + agentes.

## Raíz activa de código
Todo código del Router que se integra en este plan vive bajo:
`router inteligente universal/`

Biblioteca donor/open source:
`router inteligente universal/Componente open soure router inteligente universal/`

## Núcleo de conexión
`Enchufe Gate -> RedUniversal -> connector_registry -> adapters/conectores -> destinos`

DAGs y modelos no pueden alterar este ownership. Los componentes externos se reutilizan como donor/adapter/plugin, nunca como segundo orquestador paralelo.

## Separación vigente
- `red/enchufe_gate.py`: gate canónico v1.5, pendiente extensión v2 según task autorizada.
- `red/conectores.py`: HTTP/MCP/GitHub/HuggingFace/DB ya preservados y probados contractualmente.
- `red/conector_gitlab.py`: adapter GitLab v6 separado.
- `red/connector_registry.py`: registro explícito fail-closed de conectores integrados.
- `tests/`: tests contractuales separados.
- `integration/huggingface/`: auditoría/bridge HF y evidencia de modelos; prohibido inventar `model_id`.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- `GAP-HF-CATALOG-001` permanece no bloqueante hasta disponer de evidencia real de privados/endpoints HF.
