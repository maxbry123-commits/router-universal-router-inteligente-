# AGENTES — cableado de agentes

body:
  responsibility: 'Handoff de area (el registro maestro no lo copia: ver SYSTEM_WIRING_REGISTRY.yaml)'

## Detalle

Estado: DISCOVERED (cableado existente, pendiente de prueba real)
Componentes: `chat-router/agentes/` (adaptadores, agentes-yaiwes, claude-code, orquestacion, runtime) · `chat-router/plugins/agentes/`
Consumidores: selectores de la UI · orquestador · cola
Proveedores: harness DeepSeek (`chat-router/harness/`) · memoria (`chat-router/memoria/memoria-yaiwes/`) · storage (`chat-router/memoria/hf_datasets/`)
Contrato: agente -> selector -> adaptador -> harness -> herramientas -> memoria/storage
Healthcheck: dos capacidades distintas: (1) responder en modo agentico, (2) ejecutar herramientas autorizadas. No confundir seleccion de modelo con activacion de agente.
Pendiente: J07 (respuesta y herramientas), acceso real a almacenamiento y memoria, y el boton ON/OFF de cada agente
Evidencia: ninguna todavia
