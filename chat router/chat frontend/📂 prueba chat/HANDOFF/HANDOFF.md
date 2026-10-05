# HANDOFF — 📂 prueba chat

## Superficie de trabajo
- Repo: `maxbry123-commits/router-universal-router-inteligente-`
- Rama laboratorio/Preview: `devin/1791174524-isolated-five-panels`
- Producción: **NO TOCAR**
- `main`: **NO TOCAR / NO MERGE** sin autorización expresa del Director.
- Raíz de trabajo: `chat router/chat frontend/📂 prueba chat/`

## Objetivo
Mantener paneles UI YAIWES separados, versionados y desplegables en Vercel Preview. Cada panel debe poder evolucionar sin editar o romper otro panel.

## Contrato de edición
`READ CURRENT → PATCH QUIRÚRGICO → TEST → READ-BACK → PREVIEW → APROBACIÓN → NUEVA VERSIÓN`

Nunca: `reemplazar ventana completa → asumir PASS`.

## Reglas obligatorias
- NO monolito.
- NO mezclar ventanas/componentes entre paneles.
- NO MOCK presentado como funcional.
- Skill visual único: `Maxbry UI fromtend`.
- Cada ventana conserva código propio.
- Fail closed: si backend/browser no está verificado, reportar `BLOCKED_REMOTE`/`PENDIENTE`, no PASS.
- Versiones aprobadas se congelan.
- MOVE → VERIFY → DELETE para toda reorganización.
- Vercel **Preview únicamente**.

## Mapa de paneles
| Panel | Carpeta | Fuente recuperada para v001 |
|---|---|---|
| Chat | `Panel chat/` | `nuevo/panel-chat.*` |
| Configuración | `Panel configuración/` | `nuevo/panel-configuracion.*` |
| Canvas media | `Panel canvas video imágenes/` | `nuevo/panel-media.*` |
| Planificación | `Panel planificación/` | `nuevo/panel-seguimiento.*` |
| Agente Swarm | `Panel agente Swarm/` | `nuevo/panel-agentes.*` |
| Router | `Panel router/` | Sin candidato validado todavía; no crear mock |
| File | `Panel file/` | Sin candidato validado todavía; no crear mock |

## Fuente visual que se cableará en SALIDA 2
- Skill `Maxbry UI fromtend` completo.
- Imágenes/capturas asociadas.
- `ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md`.
- `plan chat y agentes en route.md` / plan DSL equivalente ubicado en `chat router/plan` según orden del Director.

El documento de especificación describe la UI a partir de 74 capturas y contiene jerarquía visual, interacciones, estados, flujos y contratos. No reemplazarlo por interpretación libre.

## Estado actual
### SALIDA 1
- [x] Crear raíz y normas.
- [ ] Colocar y verificar versiones v001 de código recuperado.
- [ ] Tras read-back/Preview, eliminar origen antiguo si corresponde.

### SALIDA 2 — NO EJECUTAR EN SALIDA 1
- [ ] Mover Skill + imágenes.
- [ ] Mover los dos documentos indicados por el Director.
- [ ] Cablear rutas definitivas en este HANDOFF y en README de cada panel.
- [ ] Limpiar archivos sueltos sólo después de read-back.

## Protección contra otras IA
Antes de modificar un panel:
1. Leer HEAD actual de la rama.
2. Leer exactamente el archivo objetivo.
3. Comparar con la última versión aprobada/checkpoint.
4. Conservar mejoras válidas concurrentes.
5. Recuperar sólo el delta perdido; nunca resetear toda la rama por defecto.

## Evidencia de cierre por panel
`HTML existe + CSS existe + JS existe + imports resuelven + sintaxis + Preview responde + móvil/desktop + consola + backend real cuando aplique`.

Sin todo lo aplicable, el estado es `PENDIENTE` o `BLOCKED`, nunca `100% PASS`.
