# Motor de ficha (solo dentro de fichas/, no toca el Router)
Pruebas: desde la carpeta fichas -> python -m motor.prueba_motor (13 pruebas, servidor falso, sin gastar cupo).
API: 4 recuperaciones (reintento, cambio de API, bloques de 8500 al llegar a 18000, peticion reducida). Timeout 90 s. Limites Groq/NVIDIA en limites.py, ventana de 24 h guardada en disco.
Tareas: 5 recuperaciones (SQLite, punto de control por paso, perro guardian interno, supervisor aparte, reactivar huerfanas al iniciar).
Mensajes al agente sin parar la tarea: python -m motor msg "texto"  (o servidor HTTP local con FICHA_TOKEN_ENTRADA).
Sellado con la clave del banco: FICHA_CLAVE_BANCO=... python -m motor.sellar sellar archivo
Pendiente: las API (se ponen en modelos-14) y el texto de los 24 goals (dag-codigo). Copias legibles sin claves para auditar: fichas/auditoria/.
