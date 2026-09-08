# coneccion huggueface Github

Centro de cómputo Hugging Face ↔ GitHub para Router Inteligente Universal.

Flujo mínimo:
`GitHub repo -> router -> HF1/HF2/HF3 -> cola -> almacenamiento HF -> resultado -> GitHub`.

Reglas:
- 3 workers lógicos `cpu-upgrade` (8 vCPU / 32 GB RAM).
- Umbral: 95% de RAM. Si un worker está >=95%, la nueva tarea pasa al siguiente.
- Si HF1, HF2 y HF3 están ocupados/saturados, la tarea queda en cola.
- Los workers se ejecutan como Hugging Face Jobs bajo demanda y terminan al acabar la tarea; no quedan consumiendo cómputo ocioso.
- GitHub conserva código/versionado. Hugging Face Storage conserva artefactos, resultados, cache y estado de trabajo.

No se considera PASS sin prueba física y evidencia de job/log/SHA/ruta.