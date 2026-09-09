# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`

## Lista única activa
1. 📌🛜 **Paso 1 — componentes + LLM/Hugging Face** — PARTIAL/CLOSED_SAFE
   - ✅ componentes movidos al code root;
   - ✅ bridge HF local auditado;
   - ✅ owner público HF: COUNT 0;
   - 🚩 GAP-HF-CATALOG-001: privados/endpoints sin `model_id` confirmado; no inventar adapters.
2. 📌 **Paso 2 — cableado + poda + código faltante** — ACTIVE
   - ✅ REUSE `red/conectores.py`; conectores HF/DB/GitLab/MCPApp/VPS/Memoria/Interno/Webhook + registry verificados;
   - ✅ `enchufe/validator_v2.py`, C05 `domain/schemas/enchufe_v2.py` y R-003 `red/red_universal.py` materializados/verificados desde fuentes canónicas;
   - ✅ C15 PATCH v1.5→v2.0 verificado: producción commit `4e256e1332d41f9177e0df4806bb749cbd1f1e54`, HF Job `6aa16ff732d5d0c22c5b0912` = `5 passed in 0.09s`;
   - 🚩 GAP-BEHAVIOR-CONTRACT-001: prohibido inferir/generar policy LLM;
   - ✅ R-004 PDF canónico identificado: `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/respaldo.py.pdf`, blob `2ee8d937493d1923b2c1e5d6cc294a1513df3c91`, origen commit `7db4e349ff3ea22be5f1b8c10a1efc46b73418aa`;
   - ✅ StrategyDelta de extracción persistido en `router inteligente universal/integration/audits/R004-PDF-EXTRACTION-AUDIT.md`, commit `f41db4710a7af645288fe1b1339fa5aba6cc894f`;
   - 🚩 GAP-R004-EXTRACTION-001: base64 confirma PDF, pero blob UTF-8 falla por binario, raw/web no materializa y runtime sin DNS; prohibido REUSE/GENERATE hasta recuperar fuente exacta;
   - ✅ auditoría donor C03: `pydantic-settings` local confirmado como `ADAPT_CANDIDATE`, README blob `84c893ab07d3282555622f69cee358686ba4ea99`, pyproject blob `21c3e4780e6da923cccf8435498930f4d9e1bece`, MIT; evidencia commit `fa787fe101858ecd2ddf02e1f9ff25238a2148ef`;
   - 🚩 GAP-C03-CONTRACT-001: arquitectura no define nombres env/campos, requeridos, defaults ni perfiles; no generar `settings.py` por inferencia.
3. 📌✅ **Paso 3 — tests integración** — PENDING
   - Hugging Face + GitHub + API + agentes;
   - exigir ruta + SHA/diff + read-back + test/log.

Cola 1×1 actual: auditar el siguiente componente P02 independiente con contrato/source suficiente. Si existe reusable: `REUSE > PATCH > ADAPT`; solo `GENERATE` cuando la arquitectura lo autorice y el contrato esté completo. R-004 queda en retry únicamente cuando exista una vía binaria autorizada materializable.
Reglas: no sobreingeniería; no añadir pasos; archivo presente ≠ integrado; PDF presente ≠ código recuperado; donor capaz ≠ contrato del Router; unit/contract PASS ≠ E2E.
