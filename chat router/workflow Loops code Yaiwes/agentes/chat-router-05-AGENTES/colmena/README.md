# T02 — Colmena YAIWES

Implementa los dos flujos definidos por el Director sin comunicación libre entre
agentes. Todos los adaptadores llaman a **nuestro Router**.

## YaiwesHive (doc 23)

`Goal → Rowboat → Hermes+OpenClaw(plan/debate) → Sheriff → Ruflo → Colmena
→ Sentinel → Hermes+OpenClaw(review) → Judge → PASS/REVISE/BLOCK`

Los planes y críticas independientes se ejecutan en paralelo cuando no existe
dependencia entre ellos.

## EngineeringLoop (doc 22)

`Request → Claude diseño → Grok ejecución → Claude review/fix ≤3
→ Meta×4 paralelo → agregador → MetaFixer → Meta×4 revalidación → PASS/REVISE`

Los cuatro revisores Meta solo inspeccionan en paralelo; un único MetaFixer
aplica correcciones.

## Router

`RouterCliente.chat(prompt, rol)` llama `/chat/send`. Con `SIMULADO=1`
no existe tráfico de red y se usan respuestas JSON deterministas para tests.

## Cierre

`SIMULADO=1 python -m pytest "chat router/05-AGENTES/colmena" -q`
