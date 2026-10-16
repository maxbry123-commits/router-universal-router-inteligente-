# HANDOFF CABLEADO — estado operativo actual

Actualizado: 2026-10-16

## Flujo vigente

```text
Chat → Router → cómputo / almacenamiento
```

El Router solo enruta y conecta. Los modelos, proveedores, selectores y DAG pertenecen a las fichas y permanecen fuera del Router.

## Router

- Space: `COMAND-CENTER-1/riu-router`
- URL: `https://comand-center-1-riu-router.hf.space`
- Hardware: `cpu-upgrade`
- CPU: 8 vCPU
- RAM: 32 GB
- Operación: 24/7
- `sleep_time = -1`

## Estado

- Router activo
- Chat → Router activo
- Cola existente sin cambios
- Almacenamiento sin cambios
- HF Router Jobs activos: 0
- HF Router Jobs programados: 0
- Router HF Job antiguo: retirado

## Dirección vigente

Fuente:

`router inteligente universal/LIVE_URL.json`

URL:

`https://comand-center-1-riu-router.hf.space`

`router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` mantiene:

```text
PAUSED=false
LIVE_URL=https://comand-center-1-riu-router.hf.space
```

## No modificar al cambiar el cómputo

- fichas
- modelos
- proveedores
- Harness
- memoria
- cola
- agentes
- DAG
- almacenamiento

El cambio de cómputo del Router debe limitarse a cambiar dónde apunta o corre el mismo Router.
