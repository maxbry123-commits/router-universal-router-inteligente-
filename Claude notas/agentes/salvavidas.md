# salvavidas (bloque4) - Router 24/7 sin GitHub Actions

Rama: bloque4-salvavidas. Nada lanzado de verdad: solo diseno, codigo y pruebas con mocks (19 pruebas OK en maquina temporal).

## Que se construyo (todo separado, lego)
- agents-yaiwes/common/guardian.py: un solo archivo autonomo, pensado para un HF Job pequeno (cpu-basic).
- plugins/lifeguard/ (ficha.json + plugin.py): acciones status / plan / relaunch. enabled_default=false. relaunch es dry_run por defecto.
- tests/test_lifeguard.py: 19 pruebas con la API de HF simulada.

## Como funciona (en palabras)
Cada 60 s el guardian mira dos cosas del Router: si responde /health (URL sacada de LIVE_URL del flag del repo) y cuanta vida le queda al Job (API de Jobs de HF).
Relanza un Router NUEVO si: no hay ninguno vivo, o /health falla 3 veces seguidas, o le quedan menos de 6 h.
Orden seguro: lanza el nuevo -> espera /health 200 -> escribe LIVE_URL en el repo (API de contenidos, conserva PAUSED) -> solo entonces cancela el viejo.
Si el nuevo no llega a sano, se apaga el nuevo y el viejo sigue. Si no se puede escribir LIVE_URL, el viejo sigue.
Vigilancia mutua: el guardian vigila al Router y se renueva a si mismo; el Router (plugin lifeguard, kind=guardian) relanza al guardian si desaparece o le quedan <6 h.
Vidas escalonadas: Router 7d, guardian 5d (no vencen a la vez). Escalera de vida igual que el lanzador actual: 7d -> 48h -> 24h si HF rechaza.
Anti-tormenta: cerrojo de 1 lanzamiento a la vez, pausa minima 600 s entre relanzamientos (tambien entre procesos: si ya hay un Job de ese tipo con <10 min no lanza), maximo 3 por hora, GUARDIAN_DRY_RUN=1 por defecto (no lanza nada).
Tokens solo por env: HF_CONTROL_JOBS_TOKEN, GH_AGENT_TOKEN (y los secretos del Router se copian del env del guardian por nombre; ninguna clave en el codigo).

## Comando EXACTO que lanzaria (sin ejecutar; `python guardian.py --print-command` lo imprime con solo nombres de secretos)
Router nuevo = HfApi(token=HF_CONTROL_JOBS_TOKEN).run_job(
  image="python:3.12", flavor="cpu-basic", timeout="7d", expose=[8000],
  command=["bash","-lc", "set -e; apt-get update -qq >/dev/null 2>&1 || true; command -v git >/dev/null || apt-get install -y -qq git >/dev/null 2>&1; git clone --depth 1 https://github.com/maxbry123-commits/router-universal-router-inteligente- /tmp/r && cd /tmp/r && pip install -q fastapi 'uvicorn[standard]' pydantic huggingface_hub cryptography pyyaml requests httpx psutil && python 'router inteligente universal/agents-yaiwes/common/router_job_persistent.py'"],
  env={"RIU_G2_GROQ_MODEL":"qwen/qwen3.8-27b","RIU_JOB_LIFETIME_S":"604800"},
  secrets={GITHUB_TOKEN, HF_CONTROL_JOBS_TOKEN, HF_TOKEN_1, GH_AGENT_TOKEN, RIU_ROUTER_API_KEY, RIU_AGENT_API_KEYS, NVIDIA_API_KEY_1..4, GROQ_API_KEY_2..7})  # los que existan en el env del guardian
Guardian nuevo = run_job(image="python:3.12", flavor="cpu-basic", timeout="5d", command=["bash","-lc","set -e; pip install -q huggingface_hub && curl -fsSL 'https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/common/guardian.py' -o /tmp/guardian.py && python /tmp/guardian.py"], env={"GUARDIAN_DRY_RUN":"0","RIU_JOB_LIFETIME_S":"432000"}, secrets={mismos})

## Primer arranque (lo decide el coordinador, NO hecho)
Lanzar UNA vez el guardian con los secretos en env y ademas GUARDIAN_EXPIRY_OVERRIDES=6abc32754c46ef1987032c93=2026-10-01T21:49:00Z (asi conoce la vida real del Job vivo actual, que no lleva marca de vida). Probar antes con GUARDIAN_DRY_RUN=1 (defecto) y `--once` y leer el plan.
Para que el Router vigile al guardian, alguien debe llamar cada ~5 min POST /plugins/lifeguard/call/relaunch {"kind":"guardian","dry_run":false} (o llamar plugins.lifeguard.plugin.start_peer_watch() al arrancar el Router: 1 linea).

## DIFICULTAD: la URL del Job cambia (https://<jobid>--8000.hf.jobs) y Vercel guarda RIU_ROUTER_URL fija
Solucion minima (NO implementada): un punto de entrada estable en Vercel (ruta /api/router/* o rewrite de una funcion pequena) que lea LIVE_URL del flag (raw de GitHub, cache ~30 s), y reenvie la peticion a esa URL con el token de HF. Vercel apunta siempre a ese punto estable; el guardian solo actualiza LIVE_URL. Alternativa peor: que el guardian cambie la env de Vercel y redespliegue (necesita token de Vercel y un deploy por relanzamiento).

## Pendiente / riesgos honestos
- Nada probado contra la API real de HF (solo mocks). Supuestos a verificar en el primer dry-run: JobInfo trae created_at, status.stage, command; run_job acepta los mismos argumentos que usa el workflow.
- El Job vivo 6abc... no lleva marca de vida: por eso el override de vencimiento; sin el, se supone 24 h (GUARDIAN_ASSUMED_LIFE) y relanzaria antes de tiempo.
- El guardian guarda en su Job los secretos del Router (claves de proveedores): es lo minimo para poder relanzarlo sin Actions.
- guardian.py debe estar en main (el Job lo baja por raw); hasta el merge usar GUARDIAN_REF=bloque4-salvavidas.
- Un guardian solo no basta si el plugin del Router no esta llamado: sin ese llamador el guardian puede morir sin que nadie lo relance (hoy solo se renueva a si mismo antes de vencer).
