# NCT — GAPS DEL ROUTER (repo aislado, se conecta por API/MCP después)
# Diseño fuente: si_o_si.md "BLOQUE 5 — API ROUTER" (R1-R10) + DOC3

## ESTADO GENERAL
El diseño completo del Router (10 módulos R1-R10 + Cost Optimizer) SÍ
está documentado en la bandeja con detalle. No encontré código .py real
de Fable para él (a diferencia del Kernel y el Auditor, que sí tienen
código real — ver esos documentos). El código que existe del Router es
el que yo construí en este chat, que cubre 4 de los 10 módulos de forma
parcial.

## LOS 10 MÓDULOS DEL DISEÑO vs. LO CONSTRUIDO

| # | Módulo | ¿Construido? | Qué falta exactamente |
|---|---|---|---|
| R1 | Auth & API Key Manager | Parcial (`auth.py`) | Cifrado AES-256 en reposo · rotación automática · soporte BYOK |
| R2 | Model Selector | Parcial (`seleccion.py`) | Reglas en archivo `capability.json` editable (hoy están en código) |
| R3 | Scheduler + Load Balancer | Parcial (`cola.py`+`balanceo.py`) | Agrupación en lotes (batch_size 20, overlap 5) para 200+ tareas seguidas |
| R4 | Health Check | Parcial (`balanceo.py`) | Sondeo automático cada 30s + métricas de latencia (p95) + alerta de costo/hora |
| R5 | Retry | **No construido** | Reintentos automáticos a nivel del Router (distinto de mi Recovery general del sistema) |
| R6 | Circuit Breaker | **No construido** | Cortar automáticamente un proveedor que falla repetido, antes de seguir insistiendo |
| R7 | Provider Pool | Parcial (`providers.yaml`) | Cubierto en su mayoría |
| R8 | Semantic Cache | **No construido** | Caché de respuestas parecidas para no recalcular lo mismo dos veces |
| R9 | Audit Logger | Cubierto (`ledger` hash-chain) | — |
| R10 | Monitoring | Parcial (`audit_bus` mide duración) | Panel de métricas tipo OTel completo, no solo duración |
| + | Cost Optimizer | **No construido** | Módulo dedicado a vigilar y optimizar gasto por proveedor |

## MICRO-DIAGRAMA (cómo se supone que fluye una petición)

```
Orquestador/Team Agent → POST /v1/complete
   → R1 Auth (valida+cifra) → R2 Selector (elige modelo)
   → R3 Cola+Balanceo (agrupa y reparte) → R4 Salud (evita caídos)
   → R5 Retry (si falla, reintenta) → R6 Circuit Breaker (si insiste
     mucho, corta) → R7 Pool de proveedores → R8 Caché (¿ya la
     respondí antes?) → ejecuta → R9 Registro → R10 Métricas
```

## RESUMEN: 7 gaps reales (R1-parcial, R2-parcial, R3-parcial,
R4-parcial, R5-total, R6-total, R8-total) + Cost Optimizer sin construir.
No es bloqueante — el Router ya funciona para lo básico (probado con
1000 peticiones reales); esto es lo que le falta para el diseño COMPLETO.
