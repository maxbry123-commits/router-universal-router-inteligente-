---
plugin_id: metodo-trabajo.registro-plugins.cableado
version: 1.0.0
type: method-guide
immutable_component: true
---
# Guía de registro de plugins y cableado

**crear → validar → registrar → dejar estable → conectar por plugin**.

Todo componente preparado para conexiones futuras debe dejar su plugin listo al crearse. Tras validarlo/registrarlo, no se edita el archivo para conectarlo; se conectan plugin, contrato, extension point, adapter o cable.

`REUSE > PATCH > ADAPT > GENERATE`. FAIL-CLOSED: sin source, contrato, tests o evidencia no hay PASS. No inventar APIs ni rutas. Código y documentos se registran según su tipo. Cambios incompatibles crean una nueva versión.

La arquitectura real manda. Microkernel/Plugin Architecture es referencia, no obligación de convertir todo en extensiones de un único núcleo.
