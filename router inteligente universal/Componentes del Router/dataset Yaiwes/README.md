# dataset Yaiwes

Arquitectura compacta externa de conocimiento para YAIWES. No entrena ni modifica pesos del modelo.

Documento autoritativo: [`README-AUTORITATIVO-V3.md`](./README-AUTORITATIVO-V3.md)

Plan: [`PLAN-MAESTRO-COMPACTO-V3.md`](./PLAN-MAESTRO-COMPACTO-V3.md)

Crazy Wall: [`CRAZY-WALL-DATASET-YAIWES-V3.json`](./CRAZY-WALL-DATASET-YAIWES-V3.json)

Registry: [`registry.json`](./registry.json)

Objetivo V3: **107 métodos / 1.139 registros / tiers A-B-C**. El Router trabaja contra registry/índices y hace retrieval selectivo; nunca inyecta un JSONL completo al LLM.

El mecanismo vive separado en `../Yaiwes Cognitive Control Plane/`.

El cableado del plugin universal está reservado para el último nodo `PLUGIN-999`.
