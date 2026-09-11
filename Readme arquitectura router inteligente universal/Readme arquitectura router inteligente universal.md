# Router Inteligente Universal — Arquitectura / ADN / X-Ray

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Estado ejecutivo
- CORE ejecutable: `VERIFIED_CLOSED` / 100% según RIU-0058.
- Certificación individual HF_M01..HF_M20 + regresión/E2E global final: `ACTIVE_LOOP_MODEL_CERTIFICATION`.
- Regla: `CATALOG_OBSERVED != TESTED != READY`.

## Cómo funciona el Router
`AGENTE -> API key -> FastAPI -> Auth/APIKeyGuard -> Enchufe Gate -> RedUniversal -> registry -> adapter -> destino/modelo -> verifier -> response`.
Separación preservada entre contracts/adapters/plugins/registry/loader/guards/tests.

## Tres pasos del core ya cerrados
1. Hugging Face ejecutable: conjunto verificable cerrado con PASS + FLAGS externos explícitos.
2. GitHub/C01-C23 hot-path: `C01 REST -> C20 Auth -> C15 Gate -> C17 RedUniversal -> C16 adapter -> verifier` verificado.
3. API Key Manager + E2E: 100 slots, hash-only, rotate/revoke, slot 101 fail-closed y E2E real.

## Evidencia core
GitHub Actions `RIU FAST-CLOSE` run `34582284615`, job `103208408709`: `success`, `2 passed in 6.79s`.
Commit hot-path `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E test blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Certificación HF 20 modelos
PASS/ejecución previamente verificada: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
FLAG/GAP contabilizado con evidencia previa: M04, M08, M09, M13, M14, M15, M16, M17, M19.
M18 es el único slot aún pendiente de resolución terminal individual.

## RIU-0061 — M18 individual
Job `6aa475605527934177eca1cb` (`ornith-ai/Ornith-1.5-9B-GGUF`, llama.cpp CUDA, `a10g-small`, `Q3_K_S`, ctx 512, 4 tokens, timeout 480s) terminó `ERROR exit 1`, no PASS. El log remoto mostró únicamente `HF_M18_START` porque el stderr estaba redirigido.
StrategyDelta diagnóstico `6aa475e721047bf1b0378e13`: mismo modelo/quant/flavor, ctx 128, 1 token, timeout 180s y salida directa para exponer el error. Último estado observado: `SCHEDULING / Pulling container image`.

## Pendiente obligatorio
1. Resolver terminal M18 como PASS o FLAG/GAP explícito.
2. Declarar 20/20 accounted sólo con los veinte slots contabilizados.
3. Ejecutar regresión/E2E global final.
4. Sincronizar ADN/X-Ray final.

## Criterio de cierre ampliado
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.