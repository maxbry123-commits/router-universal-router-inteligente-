# ⚠️ NO TOCAR ESTE JOB SIN AUTORIZACIÓN DEL DIRECTOR

Este es el **Job enrutador único** al que se pegan 50-100 agentes al mismo tiempo. Corre sin parar en la cuenta de Hugging Face del
Director (no en GitHub Actions), con `router inteligente universal/agents-yaiwes/common/router_job_persistent.py`.

## Reglas
- **Nadie lo apaga, lo relanza ni cambia su código sin permiso explícito del Director.**
- Se relanza automáticamente antes de que se le acabe el tiempo (los Jobs de HF tienen un máximo de duración).
- Cada 60 segundos hace `git pull` solo, para tener la versión más reciente del Router sin que haga falta apagarlo.

## Cómo pausarlo o reanudarlo de forma remota (sin apagar el Job)
Edita este archivo y haz push:
`router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag`

- `PAUSED=true` → el Router responde 503 a todo (menos `/health`) hasta que se quite.
- `PAUSED=false` → vuelve a responder normal.

El Job lo relee en cada petición — no hace falta reiniciar nada para que el cambio tome efecto.

## Cómo se conecta un agente
Cualquier agente le habla igual que a cualquier otra API del Router (mismo `/chat/route`, `/chat/jev`, etc.), apuntando a la URL de este
Job en vez de a un Job temporal de GitHub Actions. La URL exacta queda anotada en `Claude notas/` la primera vez que el Job confirme
`/health` con éxito.
