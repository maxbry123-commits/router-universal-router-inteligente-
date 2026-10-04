# Pendientes - agentes sueltos

Workflows que creo Claude en esta sesion (2026-09-27 al 2026-10-03). Estaban en .github/workflows y corrian como GitHub Actions, que el Director prohibio. Se movieron aqui SIN borrar nada: quedan como pendientes de decidir.

| Archivo | Para que servia |
|---|---|
| claude-code-espejos.yml | espejos T01-T10: agentes de codigo (Aider + modelos de NVIDIA) |
| sentinela-orquestador.yml | sentinela que verifica T01-T08 y relanza espejos (cron cada 20 min) |
| prueba-groq.yml | prueba de las claves de Groq |
| prueba-chat-e2e.yml | prueba del chat de punta a punta por el Router |
| prueba-omniroute-router.yml | prueba de OmniRoute dentro del Router. YA NO ESTABA en .github/workflows al mover (alguien la quito antes): no esta en esta carpeta |

No se movieron: sentinelas.yml (viene de otra sesion) ni riu-router-job-central.yml (lanzador del Router).
Para reactivarlos: moverlos de vuelta a .github/workflows/ (un commit).
