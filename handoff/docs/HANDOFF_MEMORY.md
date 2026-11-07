# MEMORIA Y ALMACENAMIENTO

body:
  responsibility: 'Handoff de area (el registro maestro no lo copia: ver SYSTEM_WIRING_REGISTRY.yaml)'

## Detalle

Estado: DISCOVERED (pendiente de ida y vuelta real)
Componentes: `chat-router/memoria/` · `chat-router/memoria/memoria-yaiwes/` · `chat-router/memoria/hf_datasets/` · `chat-router/plugins/hf_storage/`
Consumidores: chat · agentes · loop/cola
Proveedores: HF datasets y storage local
Contrato: plugin declara id, action, input, output, auth, timeout y errores; nunca declara escritura exitosa sin confirmacion real (ACK)
Healthcheck: escribir -> ACK -> leer -> comparar -> PASS/FAIL; y reintentar tras reiniciar el proceso
Pendiente: J10 (memoria) y J11 (storage) + persistencia tras reinicio
Evidencia: ninguna todavia
