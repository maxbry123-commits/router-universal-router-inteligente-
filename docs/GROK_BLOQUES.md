# Bloques para Grok (copiar y pegar)

## Bloque 1 — Mensaje de revisión
Grok: revisa TODO el estado actual del repo `maxbry123-commits/router-universal-router-inteligente-`, rama `main` (clonar con `--branch main`; la rama por defecto `reorganizacion` no tiene `mvp/`).
Reglas: no cambies secretos, claves ni el Router sin orden expresa; ediciones quirúrgicas (nada de reescrituras); archivos nuevos ≤100 líneas y funciones ≤25; un PASS solo con salida real de un comando. Si algo va fuera de estas instrucciones, avísalo como violación.
Revisa, en este orden, y entrega una tabla `área | PASS/FAIL | evidencia (comando y salida real) | archivo:línea del fallo`:
1. `python3 -m pytest mvp -q` (esperado: 221 pasan).
2. Frontend en navegador: `bash chat/e2e/todo.sh` (servidor local con modelos simulados; ver README en esa carpeta). Pantalla del teléfono de Antonio: 345×700. Cada suite debe terminar con 0 FAIL.
3. Cableado de CADA botón y selector del chat, en móvil y escritorio: pulsar y comprobar que cambia el estado y que el backend lo recuerda (chips IA/Agentes/System prompt, ON/OFF de cada selector, LLM tool, Agente tool, Proyectos, Conexiones, ROOM, Servidor, Pendientes, Detener, ⤢).
4. Que responde el modelo del selector (no otro): la prueba `modelos_e2e.js` y, contra el Space real, `RIU_KEY=<clave> python3 -m mvp.pruebas_vivo.conectividad`.
5. Lo que NO esté en la lista de arriba y veas roto: repórtalo con captura.
Entrega también la lista de lo que NO pudiste probar y por qué.

## Bloque 2 — Mis instrucciones: terminadas y pendientes
**Concluido (con evidencia en el repo)**
- El modelo que responde es el del selector: la identidad va justo antes del mensaje (`mvp/app.py`), prueba `modelos_e2e.js` 10/10.
- Groq y NVIDIA reales en el chat (`mvp/externos.py`, `fichas-externas.js`), pool de claves que salta la inválida; el banco guarda `GROQ_API_KEY*` y `NVIDIA_API_KEY*`.
- MCP: nombres antiguos de modelo aceptados, herramienta `salud` (commit, permisos, claves externas), el 403 dice la causa (`ia=false`).
- `/memoria` (historial y pestañas entre dispositivos), `/almacen` leer HF sin caché vieja.
- Chips IA / Agentes / System prompt con estado del servidor; LLM tool y Agente tool = los mismos permisos.
- Conexiones (con Quitar), ROOM CONFERENCIAS (turno de agentes), Servidor (`api/power.js`), checklist de Pendientes, Continuar, medios en la burbuja.
- Caja de escritura: texto+Enviar y 3 selectores (Modelo · Permisos · Herramientas); selectores de modelo dentro de la ventana Modelo; panel superior en rejilla.
- Accesibilidad WCAG 2.2 AA (0 fallos axe en 7 temas), teclado, 22 componentes RIU con prueba.
- Código dividido: `panel-chat.js` 818→408 líneas, `chat-riu2.js` 307→15.
- Auditoría forense: `docs/AUDITORIA_FRONTEND_XRAY.md`. Pruebas del chat en el repo: `chat/e2e/`.

**Faltante / dañado por Claude (Salida 2, arreglar tal cual)**
1. Simulador de pensamiento (cubo 3D + segundos) desapareció: `composer-filas.js`, `QUEDAN` no excluye `.p3d` y lo mueve a la ventana Herramientas. Debe verse junto a Enviar mientras el chat trabaja. Prueba: `node narracion.js` debe dar `cuboPensamiento: visible`.
2. Botón Detener a la vista como en la versión vieja (hoy solo aparece al trabajar).
3. Etiquetas de modo originales («Rápido — 512 tok», «Equilibrado — 1024 tok», «Pensar — 2048 tok»; las cambié sin permiso).
4. Botón «Nuevo proyecto» en Herramientas (hoy solo está en el panel superior).
5. Diseño de los selectores («amorfos»): hojas Modelo/Permisos/Herramientas con jerarquía clara; Antonio dará referencia.
6. Componentes RIU/Maxbry visibles en el chat (el skill define 22; confirmar con Antonio dónde están el 23–25).
7. Backend: pasos de herramientas en vivo en el chat de texto («el modelo iba diciendo lo que hacía»); hoy el MVP solo manda `Enviando…/En cola…`.

**Pendiente de probar (instrucciones)**
- Con el Director al lado: IA ON en el chat y luego t4 (`python3 -m mvp.pruebas_vivo.guion --modelos qwen3.8-max --pruebas t4`, las llamadas MCP salen impresas).
- t1–t6 en 10 modelos de texto más: ver `docs/PRUEBAS_MCP.md` (repartir Sol 1–4, GPT 5–7, Grok 8–10).
- Groq/NVIDIA contra el Space real: herramienta MCP `salud` → `proveedores_externos` (número de claves; 0 = falta la variable en el Space).
- Medios (imagen, voz, ASR, video) por MCP.
- Verificar en el teléfono que Vercel sirve el último commit (recargar dos veces).
- Revocar el token de HF que quedó expuesto; decidir si la rama por defecto de GitHub pasa a `main`.

## Bloque 3 — Grok Build (trazabilidad + construir/arreglar)
Contexto: frontend del chat en `chat/frontend/` (módulos ES, sin build; Vercel solo añade `?v=<sha>` con `build.sh`). Antes de tocar nada lee `docs/AUDITORIA_FRONTEND_XRAY.md` (historial de 40 commits, qué cambió Claude, qué dañó, con evidencia) y `docs/ARQUITECTURA.md`. Base «pantalla vieja»: commit `1b916a587c`.
Reglas: frontend-safety (no renombrar ids, eventos ni APIs; verificar los dos lados de cada evento); un cambio quirúrgico por vez; después de CADA cambio `bash chat/e2e/todo.sh` (debe quedar en 0 FAIL) y mirar la captura (`node phone.js` → `phone.png`, 345×700). No uses comentarios `//` en medio de una línea de código (ya cortaron `api.js` una vez). Archivos nuevos ≤100 líneas.
Construir/arreglar, en este orden, un commit por punto:
1. `composer-filas.js`: añadir `.p3d` (clase del cubo, creado en `pensando-3d.js`) a `QUEDAN` y colocarlo en la rejilla junto a Enviar (`composer-filas.css`); visible solo mientras `chat().ocupado`.
2. Botón `#btn-detener` visible siempre (como `1b916a587c`), rojo cuando hay proceso.
3. `panel-chat.js` (bloque «pildora de modo»): etiquetas originales de modo.
4. Botón Nuevo proyecto en la ventana Herramientas (`#btn-proyectos` ya existe en el panel superior; moverlo o duplicar su acción `RIU_ANCLA_ABRIR("proyecto")`).
5. Rediseño de las hojas Modelo/Permisos/Herramientas (`composer-filas.css`) y de la caja de escritura; entregar 2 propuestas con captura.
6. Hacer visibles los componentes RIU (lista en `apariencia-extra.js`).
7. Seguir dividiendo archivos grandes: `api.js` 278, `chat-ancla.js` 247, `anclaje-propuestas.js` 209, `chat-selectores.js` 208, `agentes-mirror.js` 192. Herramienta usada: extraer bloques completos sin cambiar la lógica y verificar con la batería.
Entrega: tabla `cambio | commit | PASS/FAIL de la batería | captura`.
