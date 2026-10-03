# memoria - sistema de memoria y almacenamiento (raiz unica)
Antes: chat router/04-MEMORIA. Movido el 2026-10-03. El plugin del harness vive ahora en chat router/harness plugins/memoria.
Contenido: memoria_yaiwes/ (paquete y ComponentAdapter), motores/ (servicios graphiti, graphify, agentdb + sidecar_http.py), tests/, contratos y GAPs en JSON.

Flujo: harness plugins/memoria -> Router /memoria/* -> memoria_yaiwes -> motores (graphiti, memanto, graphify, agentdb, falkordb, postgresql, sqlite, bucket HF)
Estado de cada motor: Claude notas/TRAZABILIDAD-COMPONENTES-MEMORIA-20261003.md
Nota: los registros historicos (03-ESTADO, 11-EVIDENCIA, documentos .md) siguen citando 04-MEMORIA: es el nombre que tenia cuando se escribieron.
