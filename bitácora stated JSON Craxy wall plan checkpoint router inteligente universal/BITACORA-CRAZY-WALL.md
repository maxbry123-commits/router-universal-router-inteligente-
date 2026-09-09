# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001 — BASELINE
Método de trabajo replicado desde UI YAIWES sin copiar su arquitectura funcional.

## RIU-0002 — COMPONENTES OPEN SOURCE
Componentes centralizados y luego movidos a `router inteligente universal/Componente open soure router inteligente universal/`.

## RIU-0003 — ÍNDICE / HANDOFF
Índice + Handoff C01-C23 con regla `presencia != integración`.

## RIU-0004 — PLAN 3 PASOS
1. Componentes + auditoría LLM/HF/FastAPI.
2. Cableado + poda + faltantes + filtro LLM.
3. Test HF + GitHub + API + agentes.

## RIU-0005 — HF REUSE / GAP
`huggueface/manifest.yml` + `router_hf_bridge.py` auditados. HF Job verificó `COUNT 0` modelos públicos del owner. El registry `coneccion huggueface Github/registry/repos.json` contiene 19 namespaces GitHub, no modelos HF. Privados/endpoints quedan `GAP-HF-CATALOG-001` no bloqueante; prohibido inventar `model_id`.

## RIU-0006 — P02 REUSE ENCHUFE GATE
Se materializa desde la fuente canónica documental `red/enchufe_gate.py` en `router inteligente universal/red/enchufe_gate.py` sin reescritura arquitectónica.
Commit código: `4007983f2cabecdf78198a1a7ae23aff5fcfa8ce`.
Test: `router inteligente universal/tests/test_enchufe_gate_v15.py`, commit `7328d377726dbf435cbc877d6909a5f74a9bcbb3`.
Ejecución determinista: `PASS_ENCHUFE_GATE_V15_REUSE`.

## RIU-0007 — P02 REUSE CONECTORES BASELINE
Se recupera `red/conectores.py` de la misma fuente canónica y se materializa en `router inteligente universal/red/conectores.py` sin añadir todavía el catálogo v6.
Commit código: `8dc43490cc14f21c6d09d9e3d824606868679766`.
Test: `router inteligente universal/tests/test_conectores_baseline.py`, commit `94ad8b8879c8c03b2f084ac62059bd346da6a610`.
Ejecución determinista local: `3 passed in 0.11s`.

## RIU-0008 — P02 ADAPT CONECTOR HUGGING FACE V6
Se leyó el contrato v6 y se añadió únicamente `ConectorHuggingFace` sobre el baseline, reutilizando `ConectorHTTP`; no se reescribieron HTTP/MCP/GitHub y no se inventó ningún `model_id`.
Código: `router inteligente universal/red/conectores.py`, commit `eb3d9fc2f67a33d8cf22056488ea299a2ffa7875`, blob `e7a125354e32b718a9410f1c53485dc75ca4cf15`.
Test: `router inteligente universal/tests/test_conector_huggingface_v6.py`, commit `0458b589e89d5c4ff9245528f3acb515936fa34e`, blob `90425867a0c2f1b090e6a51c584cb018fda13b18`.
Verify exact-blob: ambos blobs locales comparados contra GitHub; pytest `3 passed in 0.10s`; `PASS_CONECTOR_HUGGINGFACE_V6_CONTRACT`.
Nota: esto prueba el adapter/contrato, no un modelo privado ni endpoint remoto real.

## 3 REFUTACIONES
1. COUNT 0 público ≠ ausencia de privados/endpoints.
2. Adapter HF PASS ≠ endpoint/modelo HF real verificado.
3. Gate/conectores unitarios PASS ≠ Paso 2/3 completos.

## NEXT
Cola 1×1: siguiente conector v6 respaldado por arquitectura → PATCH/ADAPT → exact-blob test → persistir; conservar baselines verificados.
