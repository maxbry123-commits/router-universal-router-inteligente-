"""Puente del Router MVP a LOOP, Cola y Watchdog (chat router/Loop cola wachdog).
Chat y Harness llaman por HTTP/MCP: POST /plugins/<id>/call/<accion>. Aqui se resuelve ese
llamado contra plugins/<id>/plugin.py (enlace a la raiz ordenada); sin tocar router/."""
import asyncio
import importlib.util
from pathlib import Path

PLUGINS = ("nct_loop", "cola50", "watchdog48")
MIRROR = ("mirror_listar", "mirror_configurar", "mirror_agregar", "mirror_quitar")  # el selector del chat los pide a puente_chat
_RAIZ = Path(__file__).resolve().parents[3]
_CARGADOS = {}


def _cargar(plugin):
    if plugin not in _CARGADOS:
        ruta = _RAIZ / "plugins" / plugin / "plugin.py"
        if not ruta.is_file():
            raise FileNotFoundError("plugin sin plugin.py: " + plugin)
        spec = importlib.util.spec_from_file_location("loop_puente_" + plugin, ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        _CARGADOS[plugin] = modulo
    return _CARGADOS[plugin]


async def llamar(plugin, accion, cuerpo):
    if plugin not in PLUGINS:
        raise ValueError("plugin no permitido: " + str(plugin))
    modulo = await asyncio.to_thread(_cargar, plugin)
    return await asyncio.to_thread(modulo.handle, str(accion), dict(cuerpo or {}))


def en_curso():
    """Procesos del LOOP (gobernar, paralelo, motor_ejecutar) que todavia no terminan."""
    modulo = _CARGADOS.get("nct_loop")
    return sum(1 for f in getattr(modulo, "_PROC", {}).values() if not f.done())
