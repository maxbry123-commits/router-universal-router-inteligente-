# ORQUESTADOR CHAT — DELEGACIÓN 2026-09-22 8:42 PM COLOMBIA

Prioridad única: Chat YAIWES 100% funcional. El orquestador audita, registra y delega; no implementa el chat.

## Investigación aplicada
- Hugging Face Static Spaces son gratuitos.
- OAuth de Space: hf_oauth=true; en Static se usa el flujo cliente oficial de @huggingface/hub.
- Scopes requeridos para este chat: inference-api, read-repos, write-repos, jobs.
- HF Jobs: expose=[port]; Storage Buckets pueden montarse con Volume; acceso al puerto requiere token HF.
- Solo se permite máquina de 32 GB RAM para Jobs del proyecto.

## Delegación
1. agent-16-chat-space-oauth: corregir/publicar Static Space público + OAuth y smoke no-404.
2. agent-17-chat-backend-32gb: levantar Chat MVP existente en Job 32 GB, bucket /data, smoke /chat/providers 200, timeout 60m.
3. agent-18-chat-final-auditor: auditoría independiente final contra las instrucciones del Director.
4. agent-5-auditor permanece como evidencia histórica; no se usa su paper CLOSED como sustituto del smoke real.

## Gate
CHAT_100 = SPACE_LIVE + OAUTH_LIVE + BACKEND_32GB_LIVE + SEND_RECEIVE_LIVE + SELECTOR + AGENTE_SIN_AGENTE + DOCUMENTOS + GITHUB + MEMORIA/ALMACENAMIENTO + AUDITORIA_FINAL.
Nada se marca CLOSED/100% sin evidencia live.
