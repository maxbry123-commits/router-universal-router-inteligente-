# 01 — Sistema central de comunicación (HTTP + MCP)

## Respuesta corta

El sistema central **no existe como runtime**. Lo que existe es inventario y documentación.

## Qué sí existe (verificado en `main`)

| Pieza | Ruta | Tamaño |
|---|---|---|
| Registro de conexiones | `connections/registry.yaml` | 48.152 B · 38 conexiones |
| Endpoints | `connections/endpoints.yaml` | 2.644 B |
| Healthchecks | `connections/healthchecks.yaml` | 6.882 B |
| Topología | `connections/topology.yaml` | 1.154 B |
| Informe del puente | `connections/bridge_report.json` | 5.741 B |
| Registro maestro | `SYSTEM_WIRING_REGISTRY.yaml` | 19.967 B |

## Estado de las conexiones

- Las 38 conexiones (CON-001 a CON-038) están en `pending_audit`.
- Ninguna tiene `evidence` válida. El propio registro dice que un `import` no prueba una conexión real.
- Para pasar a `active` se requiere una sonda real (HTTP status, MCP `initialize`/`tools/list` o existencia de fichero) y las siete condiciones del owner.

## Lo que falta

1. Un dispatcher en runtime que lea `connections/registry.yaml` y enrute HTTP y MCP.
2. Ningún nodo del DAG actual cubre ese dispatcher. Es una decisión de diseño pendiente.
3. El proxy del Space (puertos 7860/7861/7870/1862) no lee el registro central.

## Alcance de este documento

Solo describe el estado. No implementa el dispatcher ni cambia el cableado.
