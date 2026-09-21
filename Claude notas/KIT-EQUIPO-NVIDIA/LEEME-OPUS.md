# LEEME-OPUS — usar las 4 claves NVIDIA en 4 comandos

El banco cifrado YA está en este repo (raw abajo). La única pieza que no está aquí es la CONTRASEÑA: la tiene el Director y te la pasa por su canal. Sin ella el archivo no sirve.

```bash
pip install cryptography
B=https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main
curl -O "$B/Claude%20notas/KIT-EQUIPO-NVIDIA/banco-nvidia-equipo.b64"
curl -O "$B/Claude%20notas/KIT-EQUIPO-NVIDIA/nvidia_team_client.py"
curl -O "$B/Chat%20Mvp/secret_bank/vault.py"
export RIU_TEAM_BANK_PASSPHRASE='<contraseña que te da el Director>'
python nvidia_team_client.py --bank banco-nvidia-equipo.b64 --model nvidia/nemotron-3-super-120b-a12b "Responde OK"
```

Desde Python:
```python
from nvidia_team_client import NvidiaPool, open_bank
pool = NvidiaPool(open_bank("banco-nvidia-equipo.b64", CONTRASEÑA))
print(pool.chat("nvidia/nemotron-3-super-120b-a12b", [{"role": "user", "content": "hola"}]))
```
Si una de las 4 claves se demora o falla, el cliente usa la siguiente.

Modelo recomendado: `nvidia/nemotron-3-super-120b-a12b` (trabajo en volumen). `deepseek-ai/deepseek-v4-flash-0731`, `moonshotai/kimi-k3` y `z-ai/glm-5.3-flash` se agotan con varias peticiones a la vez. Detalle y evidencia: `README.md` de esta carpeta.
Reglas: no copies ni guardes las claves; solo el banco cifrado. Si NVIDIA falla, avisa al Director.
Estado honesto: el cliente se probó con pruebas propias (abre el banco, rechaza contraseña incorrecta, respaldo entre claves); NO se ha probado desde otro equipo.
