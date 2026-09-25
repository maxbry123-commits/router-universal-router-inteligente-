# INPUT VERBATIM — Director Max — 2026-09-24 (sesión Opus, chat Vercel)
(Claves omitidas: repo público)

## Input 1
Objetivo: chat Open WebUI publicado con URL pública y conectado al Router: selector de modelos, modo con agente / sin agente, selector de cuentas de GitHub, subida de archivos anclada al almacenamiento. Solo DeepSeek V4 Flash. Nada de GPU. No tocar Job del Router ni Space del conector sin autorización. Delegar a agentes 16, 17 y 19 con cadenas de principio a fin. Nunca claves en el repo. Confirmar con el Director el camino antes de ejecutar.

## Input 2
1. El chat es en Vercel con web UI chat.
2. Plan con agentes que ejecuten; Opus solo orquesta, corrige y audita GAPs (plan básico, ahorrar tokens).
3. Un agente usa SOLO los motores de descarga y extracción para bajar componentes (no GitHub Actions, no HF Job, ningún otro método).
4. Órdenes a agentes = cadena completa de tareas de principio a fin.
5. Opus calcula tareas y tiempos; el Director activa.
6. Agente centinela/supervisor/juez/guardián con watchdog cada 10 min: vigila, resuelve GAPs, reactiva agentes parados.
7. Revisar requisitos: selector, conexiones y memoria persistente para chat y agentes.
Sin sobre-ingeniería. Solo resultados finales. Modo loop y bucle hasta terminar.

## Input 3
Usar el Open WebUI descargado (los agentes se equivocaron haciendo otro chat); reciclar código del chat hecho y todo el sistema de almacenamiento. Componentes open source con motores de descarga y extracción (~10 min), desplegar, cablear y conectar.
El chat debe poder usarse con solo IA, y con IA + agentes del repo con acceso total a Hugging Face y a todos los repos de GitHub.
Botón con selector para conectar workflows de otros repos, activarlos y darles órdenes como orquestador; mandar agentes o cablear procesos y chatear con un agente encargado. Orquestadores propuestos: Microsoft Agent Framework, Rowboat y Hermes.
Auditoría forense, verificación cruzada con lo que hay, plan simple y corto, ahorrar tokens.

## Input 4 (INICIA)
1. Vercel es solo UI; todo el código en GitHub; corre en el Router; HF como procesador.
2. Dividir en varios agentes: uno DESCARGA con los motores al destino; otro cablea y sube a HF; dividir todas las tareas en varios agentes (incluye programas del almacenamiento).
3. Hermes es un agente que está en main, descargado.
4. Todos los agentes del repo deben quedar cableados con el chat.
5. Repo `agentes`: plan pendiente para ejecutar un workflow. Agente orquestador que controle; un agente investiga el plan y prepara el cableo; destino: repo agentes raíz ➡️📂 wordflow loop code Yaiwes/ (plan de 4 objetivos). Un agente cablea y conecta todo con el orquestador del chat (MSAF, Rowboat o Hermes); investiga, cablea e informa a Opus; Opus da las instrucciones.
   Plan: https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-MAESTRO-4-OBJETIVOS.md
   Anexo: https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-ANEXO-B-SEALS-MECANISMOS.md
6. Usar Crazy Wall / bitácora / state JSON / handoff del repo; centralizar tareas y respuestas de todos los agentes.
7. Revisar la lista de componentes open source del almacenamiento (memoria permanente de agentes), organizar y delegar. "Ya tienes suficiente contexto. Inicia."
