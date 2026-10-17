# CONTRATO LOOP operativo · UI YAIWES interface

Fecha: 2026-09-08  
Repo: main · `UI YAIWES interface/`  
Estado: **vigente**. Una vuelta = un ID. Si un paso falla, no hay GitHub FROMTED.

## Opinión (registro)

El LOOP es la única forma de no mezclar 39 piezas. Sin él, se unifica, se inventa o se sube mock.  
**No empiezo CASCADE hasta que el director diga `LOOP OK`.**

## Cómo iniciamos (orden)

1. Director: `LOOP OK`
2. Grok anota este contrato en GitHub (este archivo).
3. Director: `1 CASCADE` (= RUN-01)
4. Grok corre L0→L10 **solo** RUN-01
5. Director: `OK RUN-01` o `NO` + qué cambiar
6. Solo con `OK` se copia a `02-fromted/` y se actualiza bitácora

## Schema (máquina)

Ver `LOOP-SCHEMA.json` junto a este archivo.

## Ciclo L0–L10 (siempre el mismo)

| Paso | Nombre | Qué hago | Verificación cruzada | Si falla |
|------|--------|----------|----------------------|----------|
| L0 | Recibir | ID + source path | ID está en INVENTARIO-39 | paro, no invento |
| L1 | Cargar original | abrir `01-original/` | bytes = archivo que subiste | pido el HTML/zip |
| L2 | Partir | 1 ventana = 1 archivo | no meto otra view | rehacé L2 |
| L3 | FROMTED | solo Matte/Little/Blanco; naranja Cargar/Descargar | grep lima `#d9ff43`; grep naranja fuera de Cargar/Descargar | rehacé L3 |
| L4 | Sandbox | servir HTML, 5 clicks reales | send/tab/toggle/close/open | LOOP L4 |
| L5 | Cruz | diff layout+JS vs original | funciones originales siguen | LOOP L2 |
| L6 | Mostrar | chat: original vs FROMTED + lista clicks | el director ve los 2 | no GitHub |
| L7 | Esperar | `OK <ID>` o `NO` | no asumo | si NO, L2 |
| L8 | GitHub | 01 intacto + 02 + README línea + `state.json` | commit + URLs | no seguir |
| L9 | Validar | `gh` lista el archivo; enlace en chat | 200 en blob | reparar push |
| L10 | Cerrar | bitácora `ok_ids` += ID; `pending_next` | inventario version++ | siguiente ID solo si director lo pide |

## Prohibido dentro del LOOP

- 2 IDs en la misma vuelta (salvo que el director diga `OK 2`)
- Unificar Run+Wall+chat
- Mock
- Paleta naranja HUD
- Llamar Grok Bot a un OSS
- Push a biblioteca de mocks
- Inventar HTML si no hay `01-original`

## Biblioteca (verdad 2026-09-08)

**NO** se mandó “todo el sandbox” a biblioteca.

| Dónde | Qué hay |
|--------|---------|
| Biblioteca FE GitHub | lote-01 (10) + lote-02 (10) + nota + skills-claude ref + 1 host-review. **~36 paths** |
| Biblioteca BE | stub + gitkeep. **Vacío de zips** |
| UI `01-original` | Run 3 + Wall 3 + p0x/v2/DOC1. **29 files** |
| Sandbox `public/` | **37** (incluye mocks fábrica NO aprobados) |
| Sandbox artifacts html | **73** (clones/pruebas, NO biblioteca) |
| Zips adjuntos | **NO** extraídos 1:1 a GitHub |

Los “150+” no existen como 150 archivos en GitHub. Es mezcla de zips + mocks + lotes.  
Índice: `CABLEADO-BIBLIOTECA-150.md`

Para volcar sandbox→biblioteca hace falta: `SUBE BIBLIOTECA` **y** lista de paths. Sin eso no se toca.

## Extra (P5, fuera de 39)

Anims agentes / estados / fondos / pensamiento = LOOP aparte **después** de P1–P2. Mismo L0–L10. Archivo propio, no pegado al HTML de ventana.

## Frases del director

| Frase | Efecto |
|--------|--------|
| `LOOP OK` | contrato vigente, listo para ID |
| `1 CASCADE` | arranca RUN-01 |
| `OK RUN-01` | L8–L10 |
| `NO` | vuelve L2 |
| `SUBE TÚ` | Grok push |
| `SUBE BIBLIOTECA` | solo lo listado, no mocks |
