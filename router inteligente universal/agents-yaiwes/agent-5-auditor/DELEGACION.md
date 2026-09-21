# DELEGACIÓN — lo que se manda hacer a los agentes (2026-09-21 19:01:30Z)

Sale de la auditoría de las notas del Director en 4 pasadas (17 requisitos: 6 HECHO, 11 por hacer). Prioridad del Director: SOLO el chat y los modelos de IA locales.

## chat (5)

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

## almacenamiento (1)

- [PARCIAL] **P1-05** — agent-3-router debe documentar el Space 'Mvp almacenamiento para ai' y verificar la fusión con el chat.
  - pedido: «Le conectas al chat dentro de huggueface almacenamiento su propio espacio y fusionas para crear un entorno llamado Mvp almacenamiento para ai»

## agentes (3)

- [PENDIENTE] **P1-09** — agent-4-router-smol debe crear el registro de los 50+ agentes 'Seals Team YAIWES' con su api key y pool.
  - pedido: «Vasmos a tener más de 50 agente con el nombre de agente Seals Team YAIWES»
- [AMBIGUO] **P1-08** — agent-3-router debe confirmar en una nota si el router activo es el de Fables o indicar qué código se adoptó.
  - pedido: «Necesito que revises el router en el repo de router universal usa el router que hizo Fables los code están en los archivos»
- [PARCIAL] **P1-11** — agent-8-router-local debe demostrar en local_pool que admite 50–100 espejos simultáneos.
  - pedido: «deben trabajar como mirror y duplicarse sines necesario 50 o 100 veces»

## modelos (1)

- [PARCIAL] **P1-10** — agent-8-router-local debe documentar que mirror_route NO descarga pesos locales y solo llama a la API remota.
  - pedido: «esos modelos locales no deben estar instalado a huggueface deben llamar al modelo remoto como lo indica hugguenface para no descargar el modelo»

## aceleradores (1)

- [PARCIAL] **P1-12** — agent-6-hf-nodes debe declarar el dataset y el tipo de acelerador HF asignado a cada nodo.
  - pedido: «Deben usar el dataset y los aceleradores que deberían o fueron instalados en huggueface»
