# C03 — Config inmutable — donor audit

Contrato operativo aplicado: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Nodo
`P02_WIRE_PRUNE_FILL` — cola 1×1.

## INPUT arquitectónico recuperado
Handoff C03: `Config inmutable` = `MISSING`; acción prevista `GENERATE`; regla mínima demostrada: `env única fuente de configuración`.

## Donor local auditado
- Ruta: `router inteligente universal/Componente open soure router inteligente universal/pydantic-settings/`
- README blob: `84c893ab07d3282555622f69cee358686ba4ea99`
- `pyproject.toml` blob: `21c3e4780e6da923cccf8435498930f4d9e1bece`
- Fuente upstream declarada por el propio `pyproject.toml`: `https://github.com/pydantic/pydantic-settings`
- Licencia declarada: MIT.
- Capacidad demostrada: settings management sobre Pydantic v2; dependencia `python-dotenv` disponible en el donor.

## Decisión REUSE > PATCH > ADAPT > GENERATE
`ADAPT_CANDIDATE`, no `INTEGRATED`.

No se copia el vendor ni se crea un segundo core. C03 debe ser una capa pequeña propia detrás de `domain/config` o equivalente, consumiendo `pydantic-settings` como dependencia/adaptador. El donor no define los nombres de variables, defaults, requeridos, ambientes ni política de inmutabilidad específica del Router.

## GAP-C03-CONTRACT-001
Falta un contrato explícito de campos/env de C03. La frase `env única fuente de configuración` no autoriza inventar nombres de secretos, endpoints, timeouts, defaults ni perfiles.

Decisión fail-closed: no generar `settings.py` hasta recuperar el contrato de campos o una fuente canónica del proyecto. Continuar únicamente con otra tarea P02 independiente segura si no aparece evidencia nueva.

## Council12
1. objetivo: PASS; 2. INPUT literal: PASS; 3. destino: PASS; 4. estado: PASS; 5. evidencia donor: PASS; 6. reusable: PASS; 7. arquitectura no monolítica: PASS; 8. concurrencia: PASS; 9. dependencia: PASS; 10. test: N/A para auditoría, no se reclama runtime; 11. rollback: PASS, archivo documental aislado; 12. cierre: PASS solo de auditoría.

## 3 refutaciones
1. Donor presente ≠ C03 integrado.
2. `pydantic-settings` capaz ≠ contrato de campos del Router definido.
3. Auditoría C03 PASS ≠ código C03 PASS ≠ Paso 2 cerrado.

## verify_final
PASS de auditoría/provenance. No se escribió código de producción ni se incrementa progreso por presencia.
