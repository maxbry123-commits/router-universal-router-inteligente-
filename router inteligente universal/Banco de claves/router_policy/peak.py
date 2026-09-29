"""Horario pico y precio de DeepSeek V4.1 Flash (API oficial).

Fuente verificada 2026-09-20 (documentación de DeepSeek, vía el motor de búsqueda del repo, run ws-35499662718):
- Pico: 01:00-04:00 y 06:00-10:00 UTC, de lunes a viernes, excluidos los festivos públicos chinos.
- V4.1 Flash: fuera de pico 0.15 USD entrada (fallo de caché) / 0.60 USD salida por millón de tokens; en pico el doble.
Colombia es UTC-5 todo el año (sin horario de verano).
Los festivos chinos no se calculan aquí: se pasan como conjunto de fechas UTC si se conocen.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Iterable

COLOMBIA_UTC_OFFSET_HOURS = -5
PEAK_WINDOWS_UTC = ((1, 4), (6, 10))  # [inicio, fin) en horas UTC
DEEPSEEK_V41_FLASH_PRICES = {
    "off_peak": {"input_miss": 0.15, "input_hit": 0.003, "output": 0.60},
    "peak": {"input_miss": 0.30, "input_hit": 0.006, "output": 1.20},
}


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("NAIVE_DATETIME_NOT_ALLOWED")
    return dt.astimezone(timezone.utc)


def to_colombia(dt: datetime) -> datetime:
    return _as_utc(dt).astimezone(timezone(timedelta(hours=COLOMBIA_UTC_OFFSET_HOURS)))


def is_peak_utc(dt: datetime, *, chinese_holidays_utc: Iterable[date] = ()) -> bool:
    """True si `dt` cae en una ventana pico (lunes a viernes UTC, fuera de festivos chinos conocidos)."""
    utc = _as_utc(dt)
    if utc.weekday() >= 5:  # sábado, domingo
        return False
    if utc.date() in set(chinese_holidays_utc):
        return False
    return any(start <= utc.hour < end for start, end in PEAK_WINDOWS_UTC)


def price_per_million(dt: datetime, *, chinese_holidays_utc: Iterable[date] = ()) -> dict[str, float]:
    key = "peak" if is_peak_utc(dt, chinese_holidays_utc=chinese_holidays_utc) else "off_peak"
    return {"window": key, **DEEPSEEK_V41_FLASH_PRICES[key]}


def peak_windows_colombia_text() -> str:
    return "Domingo a jueves 20:00-23:00; lunes a viernes 01:00-05:00 (hora de Colombia)"
