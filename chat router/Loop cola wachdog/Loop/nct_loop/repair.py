"""Fase 8: decisiones de recuperación; no reintenta operaciones no idempotentes ciegamente."""

def decide_repair(failures:int, *, retryable:bool, has_checkpoint:bool, authorized_fallback:bool=False) -> dict:
    if not retryable:return {'action':'BLOCK','reason':'acción no repetible sin reconciliación'}
    if failures<=2:return {'action':'RETRY_SAME','reason':'fallo transitorio, requiere nuevo recibo'}
    if failures==3:return {'action':'COMPACT_CONTEXT','reason':'comprensión del fallo y reducción de contexto'}
    if failures==4 and authorized_fallback:return {'action':'FALLBACK_AUTHORIZED','reason':'fallback expresamente permitido'}
    if has_checkpoint:return {'action':'RESTORE_CHECKPOINT','reason':'requiere restauración aprobada, no destructiva'}
    return {'action':'ESCALATE','reason':'replanificar o solicitar decisión del usuario'}
