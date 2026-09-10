# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Estado actual: `ACTIVE_LOOP`
Contrato: `tel.workflow/v3`
Modo: `FAIL_CLOSED_LOOP`

## Objetivo
Cerrar el proyecto Router Inteligente Universal sin rehacer trabajo verificado y limitando el cierre a los 3 pasos aprobados.

## Hecho y verificado
- Raíz fuente activa: `router inteligente universal/`.
- Componentes open source centralizados bajo `router inteligente universal/Componente open soure router inteligente universal/`.
- Arquitectura/Handoff/Bitácora/STATE/CHECKPOINT/PLAN/RECOVERY existentes y usados como fuentes de verdad.
- C05 Enchufe Schema/validator v2 materializado/verificado.
- C15 Enchufe Gate reutilizado/parchado v1.5→v2.
- C16 Conectores ampliado parcialmente con Hugging Face, DB, GitLab, MCPApp, VPS y Memoria.
- C17 RedUniversal reutilizado/verificado.
- HF bridge + manifest presentes.
- Hugging Face Jobs adoptado como cómputo real del proyecto.
- ConectorMemoria probado previamente en HF Job con `3 passed`.

## GAP principal
`GAP-HF-CATALOG-001`: la auditoría pública confirmó 0 modelos públicos de `COMAND-CENTER-1`, pero esto no demuestra que no existan modelos privados. Falta una ruta de credencial segura para enumerar el catálogo privado real. No se deben inventar `model_id`.

## Pasos pendientes para cierre

### PASO 1 — Hugging Face / modelos / FastAPI
1. Resolver acceso seguro al catálogo privado HF.
2. Enumerar y verificar hasta 20 modelos reales.
3. Registrar por cada modelo: `model_id`, especialidad, dataset/storage relacionado, acelerador/procesador y adapter.
4. Integrar un único gateway FastAPI del Router con adapters por modelo detrás del Enchufe Universal.
5. Usar HF Jobs como cómputo real para auditorías, procesamiento y validación.
6. Verificar cada integración con log/resultado real; no PASS por presencia.

### PASO 2 — Integración GitHub / C01-C23
1. Cruzar estado real C01-C23 contra código fuente y componentes disponibles.
2. Aplicar `REUSE > PATCH > ADAPT > GENERATE`.
3. Podar duplicación únicamente cuando esté demostrada.
4. Completar solo módulos faltantes necesarios para el flujo del Router.
5. Mantener arquitectura separada: `contracts/adapters/plugins/registry/loader/guards/tests`.
6. Todo cableado externo entra únicamente por Enchufe Universal.
7. Si hace falta descargar/extraer/copiar/mover componentes, usar exclusivamente el sistema canónico de motores en `maxbry123-commits/frontend@ef0669bbc753861bfc33b86548f3f90c0f3d8df9/➡️📂motores de descarga extracción copiado movimiento archivos fromtend/`, sin editar motores, sin LFS, sin force y con read-back+SHA.

### PASO 3 — API keys para agentes + test final
1. Crear API Key Manager propio del Router.
2. Generar una key distinta por agente.
3. Guardar solo hash/metadata; soportar revocación y rotación.
4. Entrada estándar: `Authorization: Bearer <key>`.
5. Entregar las keys una sola vez fuera de GitHub; nunca persistir plaintext.
6. Ejecutar E2E real: `agente -> API key -> FastAPI -> Enchufe -> Router -> adapter -> HF/GitHub/API -> verifier -> response`.
7. Cerrar solo con ruta + SHA/diff + read-back + test/log + URL.

## Lista única de tareas
- [ ] P01.1 Resolver catálogo HF privado.
- [ ] P01.2 Verificar hasta 20 modelos reales.
- [ ] P01.3 Registrar adapters/FastAPI/dataset/storage/aceleradores.
- [ ] P01.4 Verificar ejecución real con HF Jobs.
- [ ] P02.1 Cerrar integración C01-C23 faltante.
- [ ] P02.2 Podar duplicación y validar cableado.
- [ ] P03.1 Implementar API Key Manager.
- [ ] P03.2 Generar/rotar/revocar keys por agente.
- [ ] P03.3 Ejecutar E2E final HF→Router→GitHub/API/agentes.
- [ ] P03.4 Actualizar BITACORA + STATE + CHECKPOINT + PLAN + RECOVERY + README arquitectura y marcar `VERIFIED_CLOSED` solo con evidencia.

## Criterio de cierre
`archivo presente != integrado`
`componente descargado != cableado`
`Job success != integración completa`
`mock != test remoto real`

Estado final permitido únicamente cuando todo el E2E pase: `VERIFIED_CLOSED`.
