# HuggingFace + extracción · qué hay y soluciones

## Hechos (no alucinar)

1. El **índice** lista Transformers.js (Hugging Face) como **ZIP_ONLY**. No hay árbol extraído.  
   https://github.com/huggingface/transformers.js
2. MLC WebLLM / ONNX / wllama / LiteRT = también ZIP_ONLY (engine adapter).
3. Workflows de descarga/extracción **sí existen**:
   - `ui-yaiwes-124-download-extract-20260906.yml` — extrae a `UI YAIWES/componentes open soure UI YAIWES`, **no** a la fábrica UI.
   - `research-download-chain-*-20260903.yml` — **DEPRECATED**, no escribe.
   - `extraction-repair-guardian-20260903.yml` — guardian de partes ZIP.
4. `gh secret list` = **403**. No puedo ver si hay `HF_TOKEN`. No afirmo que el procesador HF esté conectado hasta que tú confirmes el secret en Settings → Secrets.
5. El conector de producto ya declara `huggingface` como **kind** (`connectors.js`). Eso no es login HF; es “el kernel usará este destino”.

## Soluciones

**A. Extraer lo que ya está ZIP (sin internet)**  
Montar `workflow_dispatch` que llama al extractor **ya hasheado** (`extract_existing_parts.py`) con destino:

`UI YAIWES interface/fabrica-ui/vendor/<nombre>`

Trigger: Actions → workflow → Run workflow. Sin clonar GitHub/HF en caliente (regla I04: tú subes ZIP).


**B. HuggingFace de verdad (3 capas, elige)**  

| Capa | Qué | Dónde |
|------|-----|--------|
| 1 Local | Extraer Transformers.js + WebLLM; modelos GGUF/ONNX en disco | kernel, **nunca** la ventana |
| 2 Hub | `huggingface.co` inference | token en Keychain, `token_ref` en ficha |
| 3 Datasets | el usuario elige dataset | mismo conector `kind:huggingface` |

La ventana solo manda `ABS.dispatch('model.run', {ref})`.

**C. Si el “procesador HF” ya está en Actions**  
Revisar en GitHub: Settings → Secrets (`HF_TOKEN` / `HUGGINGFACE_TOKEN`) y pestaña Actions runs de `ui-yaiwes-124`. Si hay runs verdes con extract, el pipeline vive; solo hay que **cambiar DEST** a `fabrica-ui/vendor`.

**D. No mezclar**  
HF no pinta botones. HF no es la fábrica. Es un **motor** enchufable al kernel.
