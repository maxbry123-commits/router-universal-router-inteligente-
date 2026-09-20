# SISTEMA JEV — ADICIÓN: Decider-2B-Vision (RIU-0108) — 2026-09-20

## Instrucción del Director (verbatim)
> Añade esto a el sistema jev que te di
> Mapika/decider-2b-vision existe actualmente: está basado en Qwen3.5-2B, tiene unos 2B

(La frase llega cortada en el original; se conserva tal cual. El sistema Jev que el Director entregó está en `REFERENCIAS-ADJUNTAS-INPUT-05-VERBATIM.md`, Documento 1 "METHOD 3 — JEV-LIKE" y Documento 2 "5. Decider-2B-Vision" / "NANOJEV 0.6B".)

## Verificado hoy contra Hugging Face (`hf_fs`, lectura de la ficha del modelo)
| Dato | Valor en la ficha |
|---|---|
| Repo | `Mapika/decider-2b-vision` — existe |
| Licencia | apache-2.0 |
| Modelo base | `Qwen/Qwen3.5-2B-Base` (variante visión-lenguaje de decider-2b; pesos de lenguaje v5 trasplantados) |
| Tipo | `image-text-to-text`, "decision-model, calibrated, structured-output, vision, one-pass" |
| Qué hace | imagen + pregunta de texto con opciones con letra → probabilidad calibrada sobre las opciones en un solo slot de respuesta. Sin generación. También acepta solo texto |
| Uso | `VisionDecisionModel(...).cuda()`; `slot_logits` + softmax; código en https://github.com/Mapika/decider |
| Resultados citados (300 ítems por tarea) | Pong 0.96, Breakout 0.96, Visual7W 0.89, AI2D 0.93, ScienceQA 0.95; ECE 0.02–0.07 |
| Advertencia de la propia ficha | "Not intended as a chat model" |
| NanoJev | `C-Tianyu/NanoJev` existe (público, actualizado 2026-09-17); hay conversiones de terceros (`ZeroDegress/NanoJev-bf16`, `-mlx-4bit`) |

## Cómo encaja en el sistema Jev (Método 3)
- Decider-2B-Vision = decisión de alto nivel con imagen o texto (qué pipeline, qué modelo, aceptar/reintentar). NanoJev = microdecisiones paralelas. Ambos DECIDEN; el Router AUTORIZA; el Executor EJECUTA (regla del Documento 1).
- Salida esperada: distribución de probabilidades sobre opciones cerradas (`CHOICE`, `BOOLEAN`, `SCORE`), no texto libre.
- Restricción práctica: el código de ejemplo usa `.cuda()` y ninguno de los dos aparece en el catálogo del router de Hugging Face (auditoría del 2026-09-20). Necesitan GPU propia (HF Job/Space con GPU) o local. Es trabajo del Paso 3, no del chat MVP.
- No sustituye a los LLM del chat: la ficha dice que no es un modelo de chat.
