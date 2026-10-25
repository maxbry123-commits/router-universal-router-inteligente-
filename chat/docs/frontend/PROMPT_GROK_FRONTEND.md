# Prompt para Grok — frontend pendiente (copiar y pegar)

```
Eres Grok. Trabajas con el Director (Antonio). Responde corto, en español, y solo con evidencia real.

REPO (privado): maxbry123-commits/router-universal-router-inteligente-
Clona: git clone --branch main https://github.com/maxbry123-commits/router-universal-router-inteligente-.git

TAREA: ejecuta el DSL DAG del archivo chat/docs/frontend/DSL_DAG_GROK_FRONTEND.json, nodo por nodo, respetando "depende_de".
Orden: N0 → N13 (URGENTE: bucle que congela el móvil) → N1, N2, N3, N4, N5, N6, N7 → N8 → N9 → N12.
NO ejecutes N10 (bloqueado: decisión de Antonio) ni N11 (requiere autorización de Antonio). Si N9 sale BLOQUEADO_BACKEND, déjalo así.

REGLAS (también están en el JSON):
1. Antes de modificar, inspecciona componentes, dependencias, eventos y conexiones HTTP del archivo.
2. Toca SOLO los archivos de "files_permitidos" de cada nodo. Nada de backend (chat/backend, plugins, router).
3. No toques ventana-loop.js, ventana-cola.js, ventana-watchdog.js, LOOP-wachdog-cola.json ni ventanas-control.js (los revisa otro agente).
4. JavaScript vanilla; estilo blanco con activos azules; sin emojis de color.
5. Cada cambio: primero la prueba que falla, luego el cambio mínimo, luego verde. Un commit pequeño por cambio.
6. PASS solo con salida real o captura. Si no puedes probarlo escribe NO_PROBADO y el motivo.
7. Verificación en cada nodo: node --check de los .js tocados; python3 chat/auditoria/cableado.py (FAIL=0); python3 -m pytest mvp -q (221 passed); bash chat/e2e/todo.sh (0 FAIL).
8. Sin GitHub Actions, sin PR, sin force-push. Empuja SOLO a la rama grok-frontend-2026-10-25 (no a main); Claude la fusiona, cablea y repasa la guardia.

ENTREGA: tabla "nodo | PASS/FAIL/NO_PROBADO/BLOQUEADO | evidencia | commit | archivos" y la lista final de archivos cambiados.
```

El DSL está en este mismo repo: `chat/docs/frontend/DSL_DAG_GROK_FRONTEND.json`
