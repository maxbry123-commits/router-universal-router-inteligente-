# Parche de recuperacion (2026-11-13)

Para quien retome el trabajo en una sesion nueva. Leer primero `ARQUITECTURA.md` y `HANDOFF.md`. No hay secretos en este repo: los valores viven solo en el banco de claves del Router.

## 1. Como se llega a GitHub y a Hugging Face (orden de prioridad)
1. **Conector MCP de GitHub y de Hugging Face** (el normal). Se prueba con `get_me` (GitHub) y `hf_whoami` (HF). Es lo primero y lo unico que se usa si responde.
2. **MCP propio `riu-router-github`** (herramientas Github api / Github escribir / Github leer, dentro del Router). Se usa para editar codigo cuando se prefiere el MCP propio; no se reemplaza ni se cambia.
3. **Puente Vercel (solo cuando los conectores se caen)**. Es un puente, nada mas:
   - Se crea una maquina temporal (sandbox) en el proyecto `puente`, sin teamId.
   - Dentro, los tokens de GitHub y HF se pasan por variables de entorno (se sacan del banco de claves) y nunca se imprimen.
   - Se hace la lectura/escritura en GitHub (rama `reorganizacion`) y se **detiene la maquina al terminar**.
   - En Vercel no se descarga, no se guarda ni se deja nada. Cada informe debe validar que Vercel solo fue puente.
   - Si en la sesion no aparecen herramientas de Vercel, este camino no esta disponible: avisar a Hy en una linea, no inventar otro.

## 2. Por que se cae el conector y que hacer
- Los conectores MCP se desconectan con el tiempo (token OAuth vencido, o sesion que no recibio el cambio). Senal: `ListConnectors` muestra `needs_reconnect` o `enabledInChat:false`.
- Arreglo: reconectar en claude.ai -> Ajustes -> Conectores y activarlo en el chat; si el chat no lo toma, abrir un chat nuevo con el conector encendido desde el inicio.
- Mientras tanto: no gastar tokens reintentando; usar el camino 3 si esta disponible, o esperar.

## 3. Reglas que no se rompen
- Solo se siguen las instrucciones de Hy; nada no autorizado.
- Sin GitHub Actions, sin LFS, sin jobs de HF ni Vercel para descargar. Descargas solo con los motores de descarga/extraccion de la raiz de componentes (intocables).
- Todo codigo se despliega a GitHub antes de dar el informe.
- Un solo banco de claves; las claves se sacan de ahi, no se piden de nuevo.
- El Router no lleva modelos ni API adentro: todo modelo/SDK vive en una ficha o plugin externo.
- Ediciones del Router: solo con confirmacion paso a paso. Entre edificios solo HTTP/plugins.
- Salidas a Hy: espanol simple, maximo ~10 lineas, preguntas en texto (no widgets), solo tareas resueltas o algo que necesite su aprobacion.

## 4. Estado al 2026-11-13
- Rama unica: `reorganizacion`. Ultimo commit antes de este parche: `7c74cc8f` (watchdog 2026-11-07).
- Watchdog: health del Router, MCP y chat con Groq OK; NVIDIA da error 410 (bloqueado; hay que revisar la API/llaves de NVIDIA).
- Pendientes de `HANDOFF.md` siguen abiertos (puntos 1 a 5), en especial el cargador de plugins (punto 2, decision del dueno).
- Pendiente ligado a las instrucciones del 2026-09-29: auditar el chat vs. lo escrito en el repo y registrar el input verbatim (ver `AUDITORIA-CHAT-VERBATIM.md`, que Hy tiene como archivo adjunto de ese chat; aun no esta subido aqui).

## 5. Como retomar en 4 pasos
1. Probar conectores (`get_me`, `hf_whoami`). Si fallan, seccion 2.
2. Leer `docs/ARQUITECTURA.md` y `docs/HANDOFF.md`; mirar los ultimos commits de `reorganizacion`.
3. No rehacer lo ya hecho: revisar el historial antes de pedirle algo a Hy.
4. Trabajar en la rama `reorganizacion`, un cambio por commit, con `[skip ci]`, y dejar nota en `HANDOFF.md`.
