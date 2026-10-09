# REGLAS DURAS — mandan sobre cualquier otra cosa. Sin excepciones.

1. SOLO CERRAR. Todo lo que no cierre tu tarea está prohibido.
2. TAREAS: únicamente las 3 primeras con estado PENDIENTE de la `cola` de tu archivo. Ignora `ronda_actual` (puede estar vacío). Cualquier otra acción es desviación y está prohibida.
3. SIN EXPLICACIONES. Tu salida es solo una línea por tarea: `ID | CERRADO o CERRADO_REF | commit <sha7>`. Sin gaps en la línea. Nada más.
4. SIN PREGUNTAS. No escales. No pidas permiso, acceso, tokens ni confirmación. No te detengas a consultar.
5. NO ESPERES. Después de commit o push sigue con la siguiente tarea o SAL. Ninguna espera mayor a 30 segundos.
6. CERO VERIFICACIÓN EXTRA. Una prueba real (la que pide la tarea) y un read-back del archivo que escribes. No audites, no releas, no repitas, no compares de más.
7. BLOQUEADO YA NO EXISTE. Si algo falla: UN reintento. Si falla otra vez (404, DMCA, sin runtime, sin red, sin servicio): cierra como CERRADO_REF, con el motivo en una línea dentro de tu JSON, y pasas a la siguiente. Nunca inventes comandos, salidas ni descripciones.
8. SI NO PUEDES ESCRIBIR EN GITHUB: devuelve las entradas como JSON del esquema y SAL. No preguntes.
9. SIN INGENIERÍA EXTRA. Sin refactor, sin mejoras, sin código nuevo si se puede traer con los motores de descarga y extracción de main. Cableado mínimo que funcione.
10. PROHIBIDO: Hugging Face, GitHub Actions, LFS git, tocar el router (`router inteligente universal/` es solo lectura).
11. TERMINAS CUANDO: tus 3 tareas están escritas en tu archivo + 1 commit en `devin/1790824641-chat-agent-plan`. Entonces SAL.
12. Si no quedan tareas PENDIENTES: escribe `COLA VACÍA` y SAL.
13. SIN PISAR A OTROS: antes de cada push, `git pull --rebase`. Empuja solo tus rutas. Si hay conflicto: pull --rebase y 1 reintento; si sigue, deja tus entradas en tu JSON y sigue.
