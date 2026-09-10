# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP`
Contrato: `tel.workflow/v3`
Modo: `FAIL_CLOSED_LOOP`

## Objetivo
Cerrar el proyecto Router Inteligente Universal sin rehacer trabajo verificado y limitando el cierre a los 3 pasos aprobados.

## Hecho y verificado
- Raíz fuente activa: `router inteligente universal/`.
- Componentes open source centralizados bajo `router inteligente universal/Componente open soure router inteligente universal/`.
- C05 Enchufe Schema/validator v2 materializado/verificado.
- C15 Enchufe Gate reutilizado/parchado v1.5→v2.
- C16 Conectores ampliado parcialmente con Hugging Face, DB, GitLab, MCPApp, VPS y Memoria.
- C17 RedUniversal reutilizado/verificado.
- HF Jobs adoptado como cómputo real del proyecto.
- Catálogo público: 20 modelos certificados por Job `6aa2513d5527934177ebfaad`.
- HF-M01 `Qwen/Qwen3-0.6B`: Job `6aa26cc321047bf1b0371f28` COMPLETED; `config.json`, `tokenizer_config.json`, `generation_config.json`, arquitectura Qwen3ForCausalLM, BF16 y provider live observados/verificados.

## GAP actuales
- `GAP-HF-CATALOG-001`: solo catálogo privado; no existe `HF_TOKEN` implícito en Jobs.
- `GAP-HF-M01-SERVING-001`: HF-M01 NO READY hasta validar serving compute/acelerador, dataset/storage, adapter, FastAPI y llamada real por Router.
- Gaps P02 contractuales existentes permanecen sin inventar implementación.

## Pasos pendientes para cierre

### PASO 1 — Hugging Face / modelos / FastAPI
1. Cerrar HF-M01 serving real: compute/acelerador → dataset/storage → adapter → FastAPI → llamada real/read-back.
2. Repetir cola 1×1 HF-M02..HF-M20.
3. Mantener registry `model_id→especialidad→adapter→FastAPI` y evidencia por modelo.
4. Dejar un único gateway FastAPI detrás del Enchufe Universal.
5. Resolver catálogo privado solo por ruta segura autorizada; nunca hardcodear/loggear token.

### PASO 2 — Integración GitHub / C01-C23
1. Cruzar estado real C01-C23 contra código fuente y donors.
2. Aplicar `REUSE > PATCH > ADAPT > GENERATE`.
3. Podar duplicación únicamente cuando esté demostrada.
4. Completar solo módulos faltantes necesarios.
5. Mantener `contracts/adapters/plugins/registry/loader/guards/tests` y cableado externo solo por Enchufe Universal.
6. Para descargar/extraer/copiar/mover usar exclusivamente motores canónicos de `frontend@ef0669bbc753861bfc33b86548f3f90c0f3d8df9`, sin editar, sin LFS/force, con SHA/read-back.

### PASO 3 — API keys para agentes + test final
1. Crear API Key Manager propio.
2. Key distinta por agente; guardar solo hash/metadata; revocar/rotar.
3. `Authorization: Bearer <key>` y entrega one-time fuera del repo.
4. E2E real: `agente -> API key -> FastAPI -> Enchufe -> Router -> adapter -> HF/GitHub/API -> verifier -> response`.
5. Cerrar solo con ruta + SHA/diff + read-back + test/log + URL.

## Lista única de tareas
- [ ] P01.1 Cerrar HF-M01 serving real.
- [ ] P01.2 Validar HF-M02..HF-M20 1×1.
- [ ] P01.3 Completar registry/adapters/gateway FastAPI.
- [ ] P02.1 Cerrar integración C01-C23 faltante.
- [ ] P02.2 Podar duplicación y validar cableado.
- [ ] P03.1 Implementar API Key Manager.
- [ ] P03.2 Generar/rotar/revocar keys por agente.
- [ ] P03.3 Ejecutar E2E final HF→Router→GitHub/API/agentes.
- [ ] P03.4 Marcar `VERIFIED_CLOSED` solo con evidencia completa.

## Criterio de cierre
`archivo presente != integrado`
`modelo configurado != servido`
`provider live != hot path Router`
`Job success != integración completa`
`mock != test remoto real`

Estado final permitido únicamente cuando todo el E2E pase: `VERIFIED_CLOSED`.
