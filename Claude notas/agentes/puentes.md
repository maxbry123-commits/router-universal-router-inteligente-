# puentes (Bloque 3, Paso 4)
Rama bloque3-puentes. 4 plugins separados en `router inteligente universal/plugins/` (enabled_default false, handle(action,payload)). Nucleo del Router: sin tocar.

- hf_storage (nuevo): GPT NO dejo puente (T-08 PENDIENTE, solo doc). Acciones status/list/read/write/backup_sqlite sobre el dataset privado COMAND-CENTER-1/yaiwes-hf-memoria (HF_STORAGE_REPO), API HF por HTTP, token HF_TOKEN de entorno. Storage Bucket real: pendiente (se uso el repo dataset verificado). Memoria Manus = SQLite en chat router/04-MEMORIA; backup_sqlite la copia al dataset. Falta el enlace del chat de Manus (pendiente del Director).
- hf_datasets: por llamada (hub API + datasets-server), sin guardar nada. Incluye repo_tree del dataset del repo.
- hf_skills: solo lectura de https://github.com/huggingface/skills (commit fijado abc20ae5, tomado de integration/huggingface/hf_skills_registry.json de GPT). Sin llamada real verificada.
- hf_compute: envuelve integration/hf_worker_pool.py (no reescrito). Tramos en plugins/hf_compute/config.json: umbral 80, controlador 16 GB cpu-basic, siguiente 16, salto 32 GB cpu-upgrade. Acciones status/ensure/invoke; ensure es dry-run salvo apply=true. Usuarios: Vercel chat, Hermes, OpenClaw, Orquestador, harness DeepSeek (variables RIU_*_URL propuestas por mi, no existian).

AVISOS: (1) Director habla de HF 12 GB previo y GPT de 16 GB: se usan los valores del JSON, sin decidir. (2) el pool de GPT usa umbral 85 por defecto; el JSON dice 80: fijar HF_AUTOSCALE_THRESHOLD=80. (3) No se lanzo Job ni worker alguno.
Tests: tests/test_puentes_plugins.py via .github/workflows/tmp-puentes-verify.yml (mocks).
