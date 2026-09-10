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
- Catálogo público certificado de 20 modelos: Job `6aa2513d5527934177ebfaad`.
- HF-M01 `Qwen/Qwen3-0.6B`: Job `6aa26cc321047bf1b0371f28` COMPLETED; config/tokenizer/generation validados. Sigue NO READY hasta serving+FastAPI+llamada real.

## GAP vigente
`GAP-HF-CATALOG-001` queda restringido al catálogo privado de `COMAND-CENTER-1`; no bloquea el catálogo público. `GAP-HF-M01-SERVING-001` permanece hasta validar serving compute/acelerador, dataset/storage, adapter, FastAPI y hot path Router.

## Plan único — 3 pasos
1. P01 ACTIVE — completar HF-M01 y repetir 1×1 HF-M02..HF-M20; luego gateway FastAPI único.
2. P02 PENDING — GitHub/C01-C23: cablear/podar/completar únicamente faltantes con REUSE>PATCH>ADAPT>GENERATE.
3. P03 PENDING — API Key Manager agentes + generación one-time + test E2E.

## Cableado objetivo
`agent -> API key -> FastAPI -> Enchufe -> Router -> adapter -> HF/GitHub/API -> verifier -> response`

## Adquisición de nuevos componentes
Solo sistema canónico `maxbry123-commits/frontend@ef0669bbc753861bfc33b86548f3f90c0f3d8df9/➡️📂motores de descarga extracción copiado movimiento archivos fromtend/`.

## Cierre
No declarar PASS por presencia. Exigir SHA/diff/read-back/test/log/URL. Estado actual: `ACTIVE_LOOP`.
