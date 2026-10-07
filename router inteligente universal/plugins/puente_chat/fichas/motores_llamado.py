"""Tres estrategias acotadas de llamada para las fichas del chat."""
from __future__ import annotations

MAX_LLAMADOS = 3
ESPERA_API_S = 90


def rotar_claves(cantidad, preferida=None):
    """Motor 1: hasta tres intentos secuenciales; nunca solapa peticiones."""
    if cantidad <= 0:
        return []
    orden = ([preferida] if isinstance(preferida, int) and 0 <= preferida < cantidad else [])
    orden += [i for i in range(cantidad) if i not in orden]
    return [orden[i % len(orden)] for i in range(MAX_LLAMADOS)]


def reserva_proveedor(fichas, modelo_inicial):
    """Motor 2: reserva de otro proveedor primero, luego otro modelo del inicial."""
    proveedor = fichas[modelo_inicial][1]
    candidatos = [m for m, f in fichas.items() if m != modelo_inicial and f[1] in ('groq', 'nvidia')]
    return sorted(candidatos, key=lambda m: fichas[m][1] == proveedor)[:2]


def continuar_desde_checkpoint(mensajes, checkpoint=None):
    """Motor 3: llamada de continuación con el último estado conocido."""
    base = [dict(m) for m in (checkpoint if checkpoint else mensajes)]
    base.append({'role': 'user', 'content': 'Continua desde el ultimo checkpoint. No repitas herramientas ya ejecutadas. Termina la tarea y comunica el resultado.'})
    return base
