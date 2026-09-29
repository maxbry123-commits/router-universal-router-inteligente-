# coneccion huggueface Github

Centro de cómputo Hugging Face ↔ GitHub para Router Inteligente Universal.

Flujo verificado:
`GitHub repo -> router -> HF1/HF2/HF3 -> cola -> almacenamiento HF -> resultado -> GitHub`.

Reglas verificadas:
- 3 workers lógicos `cpu-upgrade` con límite cgroup real `32000000000` bytes.
- Umbral RAM 95%; prioridad HF1→HF2→HF3; si los tres no están disponibles, estado `WAITING`/cola.
- Los workers se ejecutan como Hugging Face Jobs bajo demanda y terminan al acabar la tarea; el E2E final terminó `COMPLETED`.
- GitHub conserva código/versionado. Hugging Face Storage conserva artefactos/resultados en namespaces por repositorio mediante el bucket existente montado `/data`.
- El mapa lógico de 19 repos vive en `osquestador-auditor/main/la coneccion de todos los repos con el almacenamiento de huggueface/almacenamiento huggueface/`.

Evidencia de cierre:
- storage: `E2E_STORAGE_PASS`
- GitHub commit E2E: `16b0ecc3b530e16b9469ef3ec3ac83ba597f7186`
- HF E2E Job: `6a9f9c6f259f8e97255ee0b3` → `COMPLETED`

Estado: VERIFIED_CLOSED.
