# README-GAPS-DAG-20261107.md — Huecos reales de la carga con los motores del repo

Documento del orquestador (AGENTE 0) tras el DAG `dag.sheriff/v2` del 2026-11-07 y tras la
**segunda fase**: resolucion de los componentes bloqueados por symlinks/LFS en el ORIGEN
publicando cada uno desde un `SOURCE_REF` explicito con arbol limpio (symlinks=0, punteros LFS=0),
usando los motores canonicos intactos (blob SHA `91e6e44866` del engine, `84d566e2ee` del motor_2,
`9a21facfe1` del motor_4). Es **aditivo**: no modifica los indices del motor ni los componentes.

## 0. ESTADO ACTUAL

- Componentes publicados en su destino: **53** (27 en `Main_Skills/Frontend/`, 26 en `Main_Skills/Code/`).
- De los cuales **42 son integros** (el `tree_hash()` recalculado con la funcion del propio motor coincide con el `DOWNLOAD_EXTRACT_MANIFEST.json`).
- **3** de las 56 URLs de la cola siguen sin publicarse (seccion 3), por motivos externos o por guards del motor canonico.
- `Main_Skills/_staging/`: **0**. Indices: `README-INDICE-COMPONENTES.md`, `README-INDICE-PASSE2.md`, `README-INDICE-REFS.md`. Este documento: `README-GAPS-DAG-20261107.md`.

## 1. Componentes publicados cuyo manifest sobredeclara el contenido publicado

| Categoria | Componente | Ficheros declarados | Ficheros publicados | Delta ficheros | Bytes declarados | Bytes publicados | Delta bytes |
|---|---|---|---|---|---|---|---|
| Frontend | Recordly | 1208 | 1202 | +6 | 107149311 | 92893855 | +14255456 |
| Frontend | open-design | 14262 | 14255 | +7 | 338974396 | 338735093 | +239303 |
| Frontend | plasmic | 7730 | 7715 | +15 | 220404286 | 220400425 | +3861 |
| Frontend | playwright | 3148 | 3148 | +0 | 70157316 | 70141985 | +15331 |
| Frontend | ui | 6411 | 6405 | +6 | 51337202 | 51335893 | +1309 |
| Frontend | webstudio | 4740 | 4698 | +42 | 96947073 | 94702861 | +2244212 |
| Code | SimpleTES | 2805 | 506 | +2299 | 89175495 | 31034082 | +58141413 |
| Code | context-mode | 853 | 852 | +1 | 27349319 | 27334743 | +14576 |
| Code | firecrawl | 2218 | 2216 | +2 | 56131174 | 56122144 | +9030 |
| Code | headroom | 2790 | 2769 | +21 | 75563408 | 74290496 | +1272912 |
| Code | openevolve | 595 | 594 | +1 | 8525673 | 8521911 | +3762 |

**Total de ficheros ausentes: 2400 en 11 componentes.**

**Causa (la introdujo este DAG, en el `publish()` del motor):** `publish()` hace
`shutil.copytree(extracted, target/'code')`, es decir copia **el `.gitignore` del propio componente**
dentro de `code/`; acto seguido ejecuta `git add --sparse -- <rel>` en el clon sparse-checkout del
repo destino y **git honra ese `.gitignore`**, descartando en silencio los ficheros que coinciden.
Comprobado: el **100 %** de los ficheros ausentes (2.400 de 2.400) esta excluido por el `.gitignore`
del propio componente (`git check-ignore` sobre cada ruta ausente). El commit se pushea **antes** del
readback, asi que el arbol incompleto entra en `main` y el readback posterior revienta con
`READBACK_TREE_HASH_GAP` (error del intento 1); el reintento (`attempts: 2`) ya solo vio
`DESTINATION_EXISTS`. La base real del DAG es `2414b9029d`, donde `Main_Skills/` no existia (0 rutas).

**El contenido ausente NO se perdio:** esta integro en el bundle `_archives/` de cada componente
(`bundle_sha256` coincide con el del manifest y el CRC del ZIP es correcto).

**Remedio correcto (reextraer con el motor tal cual NO basta):** reejecutar `publish()` volveria a
copiar el `.gitignore` y a descartar los mismos ficheros, y despues volveria a chocar con
`DESTINATION_EXISTS`. La via que si funciona es **reextraer del bundle `_archives/`** y publicar con
*force-add* (`git add -f`) o neutralizando el `.gitignore` copiado. **Pendiente de ejecutar cuando el
owner lo ordene: en esta fase no se toco ningun componente ya publicado.**

Efecto secundario del mismo paso: 13 ficheros con normalizacion CRLF->LF al confirmarlos en git.

## 2. Componentes publicados que motor_2 NO/volvio a descargar en esta ejecucion

11 de los 53 componentes publicados quedaron con el guard `DESTINATION_EXISTS`: su contenido es
arrastrado de la publicacion `build(hf-combined)` anterior y en este DAG solo lo movio motor_4, que
verifica SHA-256 fichero a fichero contra el manifiesto del staging. La base de verificacion de
motor_2 es **42** componentes, no 53. Los 11 de la tabla anterior son ademas los que
tienen el shortfall de `.gitignore`.

## 3. Las 3 URLs que siguen sin publicarse (con su causa real)

| URL | Causa | Estado |
|---|---|---|
| https://github.com/thedotmack/claude-mem | `SOURCE_SPECIAL_FILE_GAP`: 7 symlinks en HEAD (`openclaw/skills/do/SKILL.md` de 2026-02-23, `openclaw/skills/make-plan/SKILL.md` de 2026-02-16, `tests/evals/read-gate/*.sh` de 2026-11-01). El `SOURCE_REF` con arbol limpio mas reciente es el **padre de 2026-02-16**, es decir un snapshot de hace 9 meses al que le faltan precisamente las skills que son el componente | pendiente de decision del owner |
| https://github.com/heygen-com/hyperframes | `SOURCE_LFS_POINTER_GAP`: **250 ficheros LFS** (patrones `*.mp4`, `*.mov`, `*.webm`, `*.png` bajo `packages/producer/tests/**`) mas 2 symlinks. La regla canonica es **NO LFS** y el motor no trae los binarios | pendiente de decision del owner |
| https://github.com/aayushsoam/motionsites.ai | **HTTP 451 DMCA**: `Repository unavailable due to DMCA takedown`. No es descargable por nadie, con ningun motor. El mismo proyecto ya esta publicado como `TheSatyam-Singh/motionsites.ai` | gap definitivo (externo) |

## 4. Componentes resueltos en esta segunda fase (6)

| Componente | Repo fuente | `SOURCE_REF` limpio | Estado |
|---|---|---|---|
| Frontend/ui-ux-pro-max-skill | nextlevelbuilder/ui-ux-pro-max-skill | `b0ebb1797ebc` | publicado y verificado por motor_2 (readback OK) |
| Frontend/caret-desktop | precious112/caret-desktop | `138992be341e` | publicado y verificado por motor_2 (readback OK) |
| Code/Scrapling | d4vinci/Scrapling | `0449bd366e31` | publicado y verificado por motor_2 (readback OK) |
| Code/ThetaEvolve | ypwang61/ThetaEvolve | `f25fa880d9cf` | publicado y verificado por motor_2 (readback OK) |
| Frontend/shadcn-labs--skills | shadcn-labs/skills | `1f06a9165d82` | publicado y verificado por motor_2 (readback OK) |
| Frontend/vercel-labs--agent-skills | vercel-labs/agent-skills | `515cc821216d` | publicado y verificado por motor_2 (readback OK) |

Motor usado: el canonico `hf_download_extract_engine.py` con blob SHA `91e6e4486692eab314be5c7130d8310d3c855397`
(identico al que declara `MOTOR-CODE-LOCK.json` en el repo `agentes`), sin modificar. La cola lleva
`source_ref` explicito por item, que es entrada documentada del motor.

## 5. Huella real de este DAG en `main`

| Tipo de commit | Numero aprox | Autor | Que toca |
|---|---|---|---|
| `build(hf-combined): publish ...` (publicacion del motor) | 54 | motor `yaiwes-hf-combined-engine` | solo `Main_Skills/` |
| `Auto-commit: ... (Auditado por Sheriff)` | 56 | `Sheriff-Agent` | solo `Main_Skills/` |

El commit unico con las 62.399 rutas no se pudo subir (la conexion se caia a los 64 s); se troceo en
commits por componente, igual que publica el motor. Ningun push fue forzado.

## 6. Recuento final

- Componentes publicados: **53**; integros: **42**; con shortfall de `.gitignore`: **11**.
- Sin publicar: **3** de 56 (seccion 3).
- `Main_Skills/_staging/`: **0**.
- Motores: blob SHA canonico intacto (6/6) antes y despues de cada fase.
- Secretos: 0 valores de token en trazas, estados, indices o arbol publicado (auth por `GIT_CONFIG_*`
  en el entorno, nunca en la URL).

> Recordatorio para la auditoria del owner: la rama por defecto del repo es `reorganizacion` y ahi
> `Main_Skills` NO existe. Hay que auditar la rama `main`.
