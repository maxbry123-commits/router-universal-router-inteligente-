# Orquestador chat/router (Grupo 1 y Grupo 2)

Solo vale lo que está en este archivo. Lo que no está aquí NO se hace.

## Centinelas (regla única)
- Centinela 1 lee la lista de instrucciones de Antonio. Si la salida no es una instrucción de Antonio: BLOQUEA.
- Centinela 2 vuelve a leer la misma lista. Si no está en las instrucciones del chat: BLOQUEA.
- Solo si los dos dicen PASA, se manda la salida.
- Lista de instrucciones: archivo único, copiado palabra por palabra con el número de mensaje.

## Reglas fijas
- No tocar Hugging Face ni el dataset.
- No escalar a Antonio. No stop. Loop hasta terminar.
- El orquestador delega, no ejecuta. Lo que se delega se hace en la PC del orquestador; se usa la PC solo si es necesario y se borra al terminar.
- Claves (GitHub, Sol GPT, Grok): el agente solo abre la ventana de login y Antonio las pone. Nunca se pegan claves en el chat.
- Sol prepara el prompt de cada investigación. El orquestador no escribe prompts de investigación.
- La fuente de la verdad vive en GitHub (no en la PC, no en HF).
- Todo código monolítico largo se divide en partes.
- El prompt no se reduce nunca (es ley): solo se organiza y se revisa el cableado.
- Responder a Antonio en español, corto.

## Estructura
- Repo: maxbry123-commits/router-universal-router-inteligente-, rama reorganizacion.
- Raíces nuevas: `raiz_router/` (Grupo 1) y `raiz_fichas_prompt/` (Grupo 2). Cada equipo trabaja solo en su raíz.
- Equipo: 2 centinelas, 3 validadores, refactorizador y 1 orquestador. Sin ejecutores.

## Grupo 1: router
- Router mínimo: cómputo, almacenamiento, transporte (MCP/HTTP) y control de la SDK. Lo demás va a plugins con el enchufe universal (Fables plugins).
- Chat de Sol: "📌 sol Grupo 1".

## Grupo 2: fichas y prompt
- Lo hace el Grok Bot de planeta123usa@gmail.com, por la web grok.com (sesión de esa cuenta).
- Chat de Sol: "🚀 sol grupo 2".
- Raíces: fichas 1-5 sin duplicados, prompt (solo organizar), motores y sistema que envuelve las fichas.
- Podar hacia un MVP: antes de borrar un archivo se da su trazabilidad a Grok y a Sol, y solo se borra si los dos aprueban.

## Método por archivo (ambos grupos)
1. Pedir a Sol un archivo de código por salida.
2. Descargarlo a la PC.
3. El equipo lo revisa (centinelas y validadores).
4. Subirlo a GitHub de inmediato.
5. Borrarlo de la PC. Sin esperas: es un ciclo.

## Pasos en curso
- Paso 1: revisar los 2 chats de Sol. Sol hace los README de arquitectura de Router, Fichas y System prompt. Los centinelas revisan que estén bien hechos. Base: la arquitectura de Claude y las instrucciones de Antonio.
- Paso 2: el Grok Bot de planeta123usa (Grupo 2) hace primero la investigación, con un prompt preparado por Sol, y la guarda como README en su raíz. Es el archivo de información base.
