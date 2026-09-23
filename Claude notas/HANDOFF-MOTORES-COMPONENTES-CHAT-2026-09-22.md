# HANDOFF OBLIGATORIO — COMPONENTES DEL CHAT SOLO POR MOTORES CANÓNICOS

Fecha: 2026-09-22
Prioridad: CHAT YAIWES.
Rol de Claude/orquestador: audita, decide y delega. Los agentes ejecutan.

## Regla obligatoria
Todo agente dedicado al chat que necesite DESCARGAR, EXTRAER, COPIAR o MOVER un componente externo DEBE usar exclusivamente los motores canónicos ya existentes en main.

PROHIBIDO como mecanismo de adquisición de componentes:
- GitHub Actions para descargar/instalar componentes.
- git clone directo del agente.
- git fetch directo del agente.
- curl/wget directo del agente.
- pip/npm/pnpm/yarn usado por el agente para adquirir código fuente/componente externo.
- APIs propias, scripts nuevos de descarga o cualquier otro downloader.
- editar/parchear/refactorizar los motores.

Si un componente falta y no puede obtenerse con los motores: FAIL_CLOSED = MOTOR_ONLY_COMPONENT_GAP.

## Motores canónicos de main
Raíz:
`➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/`

1. Descarga + extracción:
`📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`

2. Cola de descarga + extracción:
`📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`

3. Extracción ZIP:
`➡️📂 Motor de extracción zip/motor_1_extract_only.py`

4. Copia por lotes:
`➡️📂motor de copiar archivos/motor_3_copy_batches.py`

5. Movimiento por lotes:
`➡️📂motor de moves archivos/motor_4_move_batches.py`

6. Skill canónico:
`➡️📂 skills descargar extraer zip copiar mover archivos readme.md`

## Reglas de ejecución
- Motores INTOCABLES.
- Destino explícito por operación; no inferir destinos.
- Sin LFS, sin force push, sin sobreescritura silenciosa.
- PASS solo con read-back y hashes verificados.
- El agente puede preparar únicamente la entrada/cola para el motor y ejecutar el motor exacto; no puede sustituirlo.
- Los agentes 16, 17 y 18 NO descargan componentes por su cuenta.
- Si requieren un componente, deben registrar COMPONENT_REQUEST con source_repo/source_ref/slug/destino y esperar/usar el agente dedicado de componentes del chat.

## Agente dedicado
`agent-19-chat-components-motors` es el único agente del chat autorizado a adquirir componentes externos.
Su trabajo es recibir COMPONENT_REQUEST y ejecutar los motores canónicos. No descarga por otro método.

## Criterio PASS
COMPONENTE = MOTOR_CANONICO + DESTINO_EXPLICITO + VERIFIED_CLOSED + READ_BACK + HASH_OK.
