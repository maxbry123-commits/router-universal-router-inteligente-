# 📂 memoria/ — Almacenamiento y memoria del sistema

Raíz única de memoria y almacenamiento. Todo lo que guarda, indexa, recupera o audita memoria vive aquí.
Estado: en recepción. Pendiente de decisiones del owner (ver `HANDOFF.md`).
Frente: Claude Code 4 (pendiente). Anexo de input block: `ANEXO_INPUT_BLOCK.md`.

## Mapa de la raíz

| Carpeta / archivo | Función | Estado |
|---|---|---|
| `memoria-yaiwes/` | Motor de memoria multi-backend: SQLite como fuente de verdad, Qdrant como índice derivado, adaptadores Graphiti, Memanto, Graphify. | Código existente. No conectado al runtime del chat. |
| `hf_datasets/` | Plugin de datasets de Hugging Face. | Código existente. |
| `componentes/` | Componentes vendorizados: memanto, graphiti, graphify, chroma, qdrant, redis, postgres, asyncpg, aiomysql, llama_index, Sentence-Transformers, phoenix, prometheus, PyGithub. | Vendorizados. No conectados. |
| `arquitectura/` | Documentos de arquitectura previos del owner. | Referencia. |
| `subir-code/` | Notas de subida de código. | Referencia. |
| `README-DOS-SISTEMAS-DE-MEMORIA.md` | Descripción de los dos sistemas de memoria existentes. | Referencia. |
| `ANEXO_INPUT_BLOCK.md` | Input block 1 a 1 del frente de memoria. | Recepción. |
| `HANDOFF.md` | Handoff de la raíz. | Vigente. |

## Dónde está la memoria que sí corre hoy

- Memoria del chat: JSON por scope en el bucket de Hugging Face, expuesta por `chat-router/chat/backend/mvp/memoria.py`.
- Tools del Harness DeepSeek: `memoria`, `almacen`, `yaiwes_md`, `pendientes`, `sala`.
- Motor multi-backend (`memoria-yaiwes/`): existe, tiene pruebas, pero no lo importa ningún módulo del runtime.

## Principios de diseño acordados (fuentes en el anexo)

- El modelo razona. El runtime controla. La memoria recuerda. El recuperador encuentra. El auditor cuestiona. El consolidador conecta. El checkpoint recupera. La política autoriza.
- La LLM no escribe directamente en memoria canónica: pasa por normalizador, validación de esquema, auditoría y delta de estado.
- Fuente original siempre conservada; la síntesis es una capa derivada.
- Un recurso solo se usa si está AUTORIZADO, no solo REGISTRADO: DISCOVERED → REGISTERED → HEALTHY → AUTHORIZED.

## Qué no está decidido

Ver `HANDOFF.md` §5 (preguntas abiertas). En resumen: fuente de verdad única, qué componentes se activan, y si `memoria-yaiwes` se conecta al Router o queda en cuarentena.
