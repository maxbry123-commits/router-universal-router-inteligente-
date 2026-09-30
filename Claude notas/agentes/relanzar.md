# relanzar (2026-09-30) - BLOQUEADO, no se lanzo Job nuevo

Lanzamiento copiado de riu-router-job-central.yml: python:3.12, bash -lc (git clone --depth 1 de main + pip + router_job_persistent.py), cpu-basic, timeout 7d (fallback 48h/24h), expose 8000.
Job vivo 6abc32754c46ef1987032c93: RUNNING, intacto. Spec solo muestra nombres de secretos, no valores.

Secretos que tengo: HF_TOKEN_1 (HF2), HF_CONTROL_JOBS_TOKEN (HF), GH_AGENT_TOKEN (GH), GITHUB_TOKEN (GH).
FALTAN (solo existen como secretos de GitHub, ilegibles): NVIDIA_API_KEY_1..4, GROQ_API_KEY_2..7, RIU_ROUTER_API_KEY, RIU_AGENT_API_KEYS.
Sin ellos el Router nuevo no tendria modelos ni auth; no se inventaron valores. Nada cancelado, flag sin tocar, Vercel sin tocar.
