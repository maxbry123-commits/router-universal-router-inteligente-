# Puente ChatGPT → Router (50 secciones)

Usa tu plan de ChatGPT (kit oficial Sign in with ChatGPT) para 50 secciones del Router: cada una con instrucciones, historial, memoria, modelo y herramientas; varias en paralelo; caché de respuestas repetidas.

Flujo oficial (guía OpenAI "Self-hosted VMs"):
1. En tu teléfono (Termux): `npm run preparar`, luego `RIU_BANCO_CLAVE=… PUENTE_URL=… PUENTE_CLAVE=… node login-local.mjs A`. Abres el enlace, entras y autorizas el plan.
2. El script cifra la credencial con la clave del banco y la envía al puente (`/perfiles/A/importar`). El ID de máquina del puente no se toca.
3. El puente renueva la sesión solo. Sin API key.

Rutas (cabecera `x-puente-clave`): `GET /estado`, `GET /proyectos`, `PUT /proyectos/proyecto-07`, `POST /proyectos/proyecto-07/chat {texto, chat}`, `POST /proyectos/proyecto-07/memoria {nota}`, `POST /paralelo {proyectos, texto}`.
Variables: `RIU_BANCO_CLAVE`, `PUENTE_CLAVE`, `PUENTE_PERFILES`, `PUENTE_PROYECTOS` (50), `PUENTE_DATOS`, `PORT`.
Estado: código escrito; falta compilar y probar con una sesión real.
