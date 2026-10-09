# Motor de fichas (solo dentro de fichas/, no toca el Router)
Pruebas (job HF 16 GB, no Vercel): python -m motor.prueba_motor y python -m motor.prueba_fichas (FICHAS_DIR=carpeta fichas; FICHA_CLAVE_BANCO para abrir los sellos).
Piezas: api_engine (4 recuperaciones de API, 90 s, bloques de 8.500), tareas (5 recuperaciones), puerta + puerta.config.json (cola global), locks (candados entre fichas), ficha_os (mini-sistema por ficha), memoria (referencia al Harness), sellar (cifrado con la clave del banco).
GAPS: conectar_harness (memoria), RIU_DEEPSEEK_HARNESS_URL (ejecutor real), texto de los 24 goals.
