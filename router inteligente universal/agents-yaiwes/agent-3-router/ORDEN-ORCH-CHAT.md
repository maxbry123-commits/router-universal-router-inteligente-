# ORDEN ORCH-CHAT → agent-3 (P1) — post #47 FAIL (URL inventada 404)

**META:** space_url REAL alcanzable · opción 3 Static+OAuth+Inference · Job 32GB APLAZADO

## Gap #41/#47
output.txt inventó `https://huggingface.co/spaces/riu-chat-yaiwes` → HTTP 404 (sin owner). Paper CLOSED prohibido.

## Orden (ejecutar, no reescribir)
1. `python_exec` el `publish_live.py` YA en results/ (GOLDEN opción 3: create Static Space `{HF_USER}/riu-chat-yaiwes` + OAuth inference-api). **CERO regeneración del .py.**
2. Smoke: GET space_url con owner → HTTP ≠404.
3. Escribe `space_url` completo en crazy_wall como `PENDING_VERIFY`. **PROHIBIDO status CLOSED** (orch cierra tras verificar live).
4. NO lances Job esta ronda.
5. Documenta gap: Job 32GB aplazado.

## PASS
space_url con owner + HTTP live ≠404 en output.txt. Wall PENDING_VERIFY (no CLOSED).
