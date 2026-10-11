# HANDOFF — frontend del chat

**Para el siguiente agente.** Lee primero `README.md` (mapa de paneles, ventanas, cableado, GAP y checkpoint).

## Estado
- 5 paneles: Chat, Canvas, Seguimiento, Archivos (+ Proyecto), Configuración. Cada uno con su HTML y su JS.
- Ventanas nuevas del chat, cada una en su archivo: Workflow Loops code Yaiwes, Constitución sentinela, Banco de claves.
- Lo nuevo no cambia el envío del chat mientras no haya nada encendido.
- Nada de esto se ha visto funcionando en pantalla: el entorno de trabajo no abre navegador. Verificar con capturas del Director.

## Siguiente (en orden)
1. Pedir capturas al Director de: pestañas con X, botón de enviar, pastillas workflow / constitución / claves, ventana de Anclaje con «Anclar a», panel Configuración, pestaña Proyecto.
2. Etapa de imágenes del skill: pedir que las suba (no se leen desde el túnel). Flujo del Director: buscar → mejorar diseño según el skill → 0 fricción → mejorar 10 veces y revisar → revisar de nuevo → función → integrado al backend → siguiente.
3. Cerrar los GAP del README (adaptador real de workflows, SDK de agentes remotos, los 2 botones de anclaje que faltan, `/vault` expuesto, generación de imagen/video en Canvas).

## Cómo comprobar sin romper (sin navegador)
- `node --check <archivo>.js` en cada JS.
- Importar `shell.js` con un DOM de mentira para detectar errores de carga entre módulos.
- Pruebas de lógica pura: `contexto.js` (prefijo, bloques `[[WF:…]]`, `/wf`) y `bloqueo-pin.js`.
- Subir en **un solo commit** por tanda y confirmar que el contenido de GitHub es idéntico al preparado.

## Cuidado
- No tocar nada fuera de `chat router/chat frontend/` (y el backend del chat si hace falta).
- Vercel solo como puente. Límite de despliegues: no subir commits sueltos.
- Edge puede guardar archivos viejos: `vercel.json` ya pide revalidar; si algo «desaparece», probar en otro navegador antes de revertir.
- La llave de GitHub usada para escribir debe cambiarse cuando termine la tanda.
