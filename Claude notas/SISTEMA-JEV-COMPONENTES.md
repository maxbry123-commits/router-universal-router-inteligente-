# SISTEMA JEV — COMPONENTES (registro con Decider-2B-Vision) — 2026-09-20

INSTRUCCIÓN DEL DIRECTOR (verbatim, INPUT-06): "Añade esto a el sistema jev que te di / Mapika/decider-2b-vision existe actualmente: está basado en Qwen3.5-2B, tiene unos 2B"
Documento fuente del sistema Jev: `REFERENCIAS-ADJUNTAS-INPUT-05-VERBATIM.md` (textual; ver su fe de erratas).

## Componentes del sistema Jev-like (Método 3)
| Componente | Rol | Base | Licencia | Verificado 2026-09-20 |
|---|---|---|---|---|
| `Mapika/decider-2b-vision` (Decider-2B-Vision) | Coordinador de alto nivel: estado + imagen + pregunta + opciones → probabilidades en una pasada | `Qwen/Qwen3.5-2B-Base` (etiqueta del Hub; el Director la nombra "Qwen3.5-2B") | Apache-2.0 | Existe. `image-text-to-text`, 105 descargas, 7 likes, actualizado 2026-09-17 |
| `C-Tianyu/NanoJev` (0.6B) | Microdecisiones paralelas (choice / boolean / score, 2-255 candidatos) | `Qwen/Qwen3-0.6B` | Sin etiqueta de licencia en el Hub (el adjunto dice MIT; no verificado en el repo de pesos) | Existe. 277 descargas, 40 likes, actualizado 2026-09-17 |
| Jevlike (`vinnylarouge/jevlike`) | Modelo pequeño texto + N opciones → distribución | propio | MIT (según adjunto) | No verificado |
| Verdict / OpenJev 151M (`Heman10x-NGU/Verdict-open-jev`) | Decisor no autoregresivo (ModernBERT 151M) | ModernBERT | (adjunto) | No verificado |
| OpenJev (`TheoLeeCJ/openjev`) | Capa externa: lee logits de un modelo abierto y devuelve decisiones tipadas | modelo abierto (p. ej. Qwen) | MIT | Repo existe: 2,025 estrellas, push 2026-09-19 |
| System One Lite (`snellingio/system-one`) | Capa externa: servidor HTTP + SDK Python/JS con Choice/Score/Noul | Qwen open-weight | MIT | Repo existe: 39 estrellas, push 2026-09-18 |

## Reglas del sistema (del adjunto)
- AI = decide; ROUTER = autoriza; EXECUTOR = ejecuta. Decider y NanoJev nunca ejecutan herramientas: devuelven probabilidades tipadas y el Router determinista decide.
- Decider-2B → decisiones de alto nivel (qué hacer / qué LLM usar / aceptar-combinar-investigar-escalar). NanoJev → muchas microdecisiones (herramienta A/B, ¿aceptar patch?, ¿ejecutar test?, ¿llamar LLM grande?).
- Interfaces de decisión: CHOICE, BOOLEAN, SCORE (distribución completa).

## Estado
REGISTRADO, NO INTEGRADO. Ninguno de estos modelos aparece en el catálogo del router de Hugging Face (138 modelos, run `35489878690`), así que su ejecución requiere runtime propio (local o endpoint dedicado). Se integran en la Fase 7 del plan (`PLAN-MAESTRO-CHAT-MVP.md`), después de cerrar el chat.
