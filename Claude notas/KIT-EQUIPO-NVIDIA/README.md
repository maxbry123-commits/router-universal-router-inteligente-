# KIT EQUIPO NVIDIA — para que otro equipo (Sonnet) trabaje ya con 4 claves NVIDIA

## Qué recibe el equipo (por el Director, NO desde este repo)
1. `banco-nvidia-equipo.b64`: banco cifrado con 4 claves NVIDIA (`digi-maxbry`, `movistar-briseida`, `wow-maxbry`, `wow-brisa`). Es un banco APARTE del maestro: no tiene Hugging Face ni GitHub.
2. La contraseña de ese banco (la da el Director al equipo por su propio canal). Sin ella el archivo no sirve.

## Cómo usarlo (5 pasos)
1. `pip install cryptography`
2. Bajar `vault.py` del repo: `Chat Mvp/secret_bank/vault.py` (público).
3. Bajar `nvidia_team_client.py` (esta carpeta).
4. `export RIU_TEAM_BANK_PASSPHRASE='…'`
5. `python nvidia_team_client.py --bank banco-nvidia-equipo.b64 --model nvidia/nemotron-3-super-120b-a12b "Responde OK"`
Desde Python: `NvidiaPool(open_bank(banco, contraseña)).chat(modelo, mensajes)`. Si una clave tarda o falla, usa la siguiente (respaldo automático).

## Qué modelos usar (evidencia real, 2026-09-20, runner de GitHub)
| Modelo en NVIDIA | Resultado |
|---|---|
| `nvidia/nemotron-3-super-120b-a12b` | Funciona (claves 3, 4 y 5 en 1-2 s; claves 1 y 2 dieron error 503). USAR ESTE PARA TRABAJO EN VOLUMEN. |
| `deepseek-ai/deepseek-v4-flash-0731` | Responde con una sola petición (claves 1, 3, 4, 5), pero con 10 peticiones a la vez se agota el tiempo. Máximo 1-2 en paralelo. |
| `moonshotai/kimi-k3` | Se agota el tiempo con carga. Mejor por Hugging Face. |
| `z-ai/glm-5.3-flash` | Se agota el tiempo con carga. |
| `moonshotai/kimi-k2.6` | No existe en NVIDIA (404). |
| `minimaxai/minimax-m2.7` | Retirado por NVIDIA (410). MiniMax M3 funciona por el router de Hugging Face. |
La clave 2 (`digi-briseida`) queda fuera del kit por inestable.

## Reglas del equipo
- No repetir, copiar ni guardar las claves; solo el banco cifrado.
- Delegar siempre con DSL DAG determinista (ver `DSL-FABLES-yaiwes-node-executor-xray-v2.md` en `Claude notas/`).
- Anotar cada instrucción del Director 1 a 1 antes de ejecutar (Claude notas + bitácora).
- Si falla NVIDIA, avisar al Director (no cambiar de proveedor sin su OK).
