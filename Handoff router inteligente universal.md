# Handoff Router Inteligente Universal

## Estado ejecutivo
Proyecto activo bajo contrato `tel.workflow/v3` / `FAIL_CLOSED_LOOP`.

## Arquitectura entendida
Router determinista: clasifica entrada, selecciona DAG fija, valida por Enchufe Universal y despacha por RedUniversal/conectores. La IA no modifica la estructura del DAG.

## Raíz fuente
`router inteligente universal/`

Raíces verificadas: `domain/`, `enchufe/`, `engine/`, `integration/`, `red/`, `tests/`, `Componente open soure router inteligente universal/`.

## Integraciones ya trabajadas
- C05 Enchufe Schema/validator v2: materializado/verificado.
- C15 Enchufe Gate: reuse/patch v1.5→v2.
- C16 Conectores: parcial, ampliado con HF, DB, GitLab, MCPApp, VPS y Memoria.
- C17 RedUniversal: reuse verificado.
- HF bridge + manifest presentes.
- HF Jobs adoptado como compute real.
- ConectorMemoria con test previo en HF Job: 3 passed.

## GAP vigente
HF catalog privado no certificado. Auditoría pública dio 0 modelos públicos; no se inventan model IDs. Falta resolver credencial segura para enumerar privados y cerrar lista real de hasta 20 modelos.

## Plan único — 3 pasos
1. P01 ACTIVE — Hugging Face: modelos reales + compute/aceleradores + dataset/storage + adapters + gateway FastAPI único.
2. P02 PENDING — GitHub/C01-C23: cablear/podar/completar únicamente faltantes con REUSE>PATCH>ADAPT>GENERATE.
3. P03 PENDING — API Key Manager agentes + generación one-time + test E2E.

## Cableado objetivo
`agent -> API key -> FastAPI -> Enchufe -> Router -> adapter -> HF/GitHub/API -> verifier -> response`

## Adquisición de nuevos componentes
Solo sistema canónico `maxbry123-commits/frontend@ef0669bbc753861bfc33b86548f3f90c0f3d8df9/➡️📂motores de descarga extracción copiado movimiento archivos fromtend/`.

## Cierre
No declarar PASS por presencia. Exigir SHA/diff/read-back/test/log/URL. Estado actual: `ACTIVE_LOOP`.
