# Router Inteligente Universal — estado operativo

Actualizado: 2026-10-16

## Función actual

```text
Chat → Router → cómputo / almacenamiento
```

El Router solo enruta y conecta el chat con el cómputo y el almacenamiento.

El Router no contiene ni decide modelos, proveedores, selectores o DAG. Esa lógica pertenece a las fichas y permanece fuera del Router, sin cambios de arquitectura.

## Runtime actual

- Space: `COMAND-CENTER-1/riu-router`
- URL: `https://comand-center-1-riu-router.hf.space`
- Hardware: Hugging Face `cpu-upgrade`
- CPU: 8 vCPU
- RAM: 32 GB
- Operación: 24/7
- `sleep_time = -1`

## Estado operativo

- Router: activo
- Chat → Router: activo
- Cola existente: intacta
- Almacenamiento: intacto
- HF Router Jobs activos: 0
- HF Router Jobs programados: 0
- Runtime del Router por HF Job antiguo: retirado

## Dirección del Router

Fuente vigente:

`router inteligente universal/LIVE_URL.json`

Dirección vigente:

`https://comand-center-1-riu-router.hf.space`

`ROUTER_JOB_PAUSE.flag` apunta a la misma dirección y mantiene `PAUSED=false`.

## Regla de arquitectura

Para cambiar el cómputo del Router se modifica únicamente el destino del Router. No se modifican fichas, modelos, proveedores, Harness, memoria, cola, agentes, DAG ni almacenamiento.
