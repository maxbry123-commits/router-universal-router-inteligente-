"""Políticas de enrutado por coste y horario (Paso 3 del Director; aquí solo la parte pura y probada)."""
from .peak import (  # noqa: F401
    COLOMBIA_UTC_OFFSET_HOURS,
    DEEPSEEK_V41_FLASH_PRICES,
    is_peak_utc,
    peak_windows_colombia_text,
    price_per_million,
    to_colombia,
)
