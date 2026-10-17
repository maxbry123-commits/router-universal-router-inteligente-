# LOOP operativo · verificación cruzada

Siempre el mismo ciclo. Si un paso falla, **no se avanza**. No hay salida de “casi”.

```
S0 IDLE  → espera ID del director
S1 INTAKE → copiar source a 01-original + hash + lista de piezas
S2 SPLIT → 1 archivo = 1 ventana, aún SIN cambiar color
S3 FROMTED → solo tokens
S4 SANDBOX → 5 clicks reales, EVIDENCE.json
S5 CROSS → original vs fromted vs skill vs INVENTARIO-39 vs bitácora
S6 SHOW → en el chat SOLO ese ID
S7 GATE → OK ID | RECHAZO ID | STOP
S8 COMMIT → GitHub 02-fromted + línea README + state.json  (solo si OK)
           ↳ vuelve a S0
```

## S4 — 5 clicks (obligatorio)

1. Abre. 2. Acción primaria. 3. Cierra/ocultar si aplica. 4. Segunda acción. 5. No rompe al recargar.

Cada click: `pass|fail` en `UI code versiones/<ID>/EVIDENCE.json`.

## S5 — cruz (5 pasadas)

1. ¿El original sigue igual (hash)?  
2. ¿FROMTED no tocó JS de negocio?  
3. ¿Tokens = ley?  
4. ¿ID existe en INVENTARIO-39?  
5. ¿Bitácora y README dicen el mismo estado?

Cualquier `fail` → S3 o S2, nunca S8.

## Comandos del director

| Texto | Efecto |
|--------|--------|
| `CICLO RUN-01` | arranca S1 de CASCADE |
| `CICLO <ID>` | arranca ese ID |
| `OK <ID>` | S7 → S8 |
| `RECHAZO <ID> <motivo>` | vuelve a S2/S3 |
| `STOP` | S0, no commit |
| `SUBE TÚ` | S8 lo empuja el agente |
| `AUDITA BIBLIOTECA` | lista sandbox vs GitHub, no fabrica |

## Cómo iniciamos (para no cagarla)

1. Este contrato ya está en GitHub.  
2. Primer ID: **RUN-01 CASCADE** (HTML tuyo).  
3. Tú escribes exactamente: **`CICLO RUN-01`**.  
4. Yo no empiezo P2/P3/P5 en el mismo turno.
