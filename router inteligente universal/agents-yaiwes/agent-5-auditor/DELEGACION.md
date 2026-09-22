# DELEGACIÓN — lo que se manda hacer a los agentes (2026-09-22 09:30:17Z)

Sale de la auditoría de las notas del Director en 4 pasadas (28 requisitos: 6 HECHO, 22 por hacer). Prioridad del Director: SOLO el chat y los modelos de IA locales.

## chat (7)

- [AMBIGUO] **P1-15** — agent-3-router debe elegir y documentar el front-end open source usado y publicar la URL pública.
  - pedido: «Necesito un acceso directo al chat busca algo Open soure como el chat de minimax o Claude que pueda usar para el chat»
- [PARCIAL] **P1-01** — agent-1-chat-hf debe añadir al selector los 4 proveedores literales del Director (DeepSeek v4 flash/pro, Kimi k3, MiniMax M3) y validar cada api key.
  - pedido: «Necesitas que pueda tu colocar los api key de mis modelos locales y los modelos de deepsek v4 flash y pro y Kimi k 3 mínimax M3»
- [PARCIAL] **P1-02** — agent-3-router debe entregar la URL del Space HF público y el repo GitHub con raíz main enlazado al chat.
  - pedido: «Que puedan operar en Github y huggueface 100%»
- [PARCIAL] **P1-13** — agent-1-chat-hf debe priorizar el chat con esos 5 proveedores y validar el orden (Nvidia → locales → DeepSeek v4).
  - pedido: «necesito resolver la prioridad de el chat con los requisitos que. Te puse como primer paso Mónico chat + deepsek v4 flash y pro + Kimi k 3+ Nvidia api + mínimax M3»
- [PARCIAL] **P1-17** — agent-1-chat-hf debe cablear vault_panel como panel persistente de Archivos/Memoria dentro de la UI del chat.
  - pedido: «añadiría una ventana/panel persistente de Archivos / Memoria»
- [PARCIAL] **P2-09** — agent-1-chat-hf debe cablear el panel Archivos / Memoria persistente dentro del mismo chat, integrado con el ingestion router.
  - pedido: «Mantendría el mismo chat, pero añadiría una ventana/panel persistente de Archivos / Memoria»
- [PARCIAL] **P2-11** — agent-1-chat-hf debe entregar el chat open source (estilo MiniMax/Claude) cableado al selector de modelos, agentes y al panel de archivos.
  - pedido: «Necesito un acceso directo al chat busca algo Open soure como el chat de minimax o Claude que pueda usar para el chat para cambiar de modelos y agente y para almacenar archivos»

## almacenamiento (8)

- [PENDIENTE] **P2-05** — agent-2-chat-hf-smol debe decidir si se instala Graphty (visualización) o se mantiene backend-only y dejarlo documentado.
  - pedido: «Graphty  → visualiza gráficamente nodos y conexiones»
- [PENDIENTE] **P2-07** — agent-2-chat-hf-smol debe instalar e integrar AgentDB como memoria especializada de los agentes y conectarla al chat.
  - pedido: «AGENTDB    → memoria especializada del agente»
- [PENDIENTE] **P2-08** — agent-2-chat-hf-smol debe elegir e instalar FalkorDB (recomendado por el propio CONTEXTO) como backend de Graphiti y entregar el conector.
  - pedido: «FalkorDB o Neo4j backend de Graphiti»
- [AMBIGUO] **P2-03** — agent-1-chat-hf debe confirmar que el SQL del Chat MVP es PostgreSQL y entregar el esquema (DDL) y la conexión real.
  - pedido: «Database principal PostgreSQL estado persistente y estructurado»
- [PARCIAL] **P1-05** — agent-3-router debe documentar el Space 'Mvp almacenamiento para ai' y verificar la fusión con el chat.
  - pedido: «Le conectas al chat dentro de huggueface almacenamiento su propio espacio y fusionas para crear un entorno llamado Mvp almacenamiento para ai»
- [PARCIAL] **P2-02** — agent-1-chat-hf debe cablear explícitamente SQL, Graphiti/Graphty y caché en el chat, con archivos de configuración por cada capa.
  - pedido: «Data base SQL Little Graphiti y graphyty Caché»
- [PARCIAL] **P2-04** — agent-2-chat-hf-smol debe cablear Graphiti como capa de memoria de conocimiento dentro del chat y entregar el módulo de conexión.
  - pedido: «Graphiti → construye/consulta la memoria de conocimiento»
- [PARCIAL] **P2-06** — agent-1-chat-hf debe cablear Redis (caché, TTL, locks, rate limits, deduplicación) al chat y entregar el módulo.
  - pedido: «Redis → caché de respuestas»

## agentes (4)

- [PENDIENTE] **P1-09** — agent-4-router-smol debe crear el registro de los 50+ agentes 'Seals Team YAIWES' con su api key y pool.
  - pedido: «Vasmos a tener más de 50 agente con el nombre de agente Seals Team YAIWES»
- [AMBIGUO] **P1-08** — agent-3-router debe confirmar en una nota si el router activo es el de Fables o indicar qué código se adoptó.
  - pedido: «Necesito que revises el router en el repo de router universal usa el router que hizo Fables los code están en los archivos»
- [PARCIAL] **P1-11** — agent-8-router-local debe demostrar en local_pool que admite 50–100 espejos simultáneos.
  - pedido: «deben trabajar como mirror y duplicarse sines necesario 50 o 100 veces»
- [PARCIAL] **P2-12** — agent-4-router-smol debe entregar la lógica de handoff/fallback entre APIs cableada al chat y a los agentes.
  - pedido: «Las 4 api de Nvidia y cerebras si no responde o los modelos no están disponibles el router Salta para mis api locales»

## modelos (2)

- [PARCIAL] **P1-10** — agent-8-router-local debe documentar que mirror_route NO descarga pesos locales y solo llama a la API remota.
  - pedido: «esos modelos locales no deben estar instalado a huggueface deben llamar al modelo remoto como lo indica hugguenface para no descargar el modelo»
- [PARCIAL] **P2-13** — agent-9-models-catalog debe certificar la cuantificación ≤26 GB de RAM y entregar el plan de caché por modelo.
  - pedido: «Modelos que deben trabajar local por máximo 26 de ram  quanrificado para no saturar el procesador + caché»

## aceleradores (1)

- [PARCIAL] **P1-12** — agent-6-hf-nodes debe declarar el dataset y el tipo de acelerador HF asignado a cada nodo.
  - pedido: «Deben usar el dataset y los aceleradores que deberían o fueron instalados en huggueface»
