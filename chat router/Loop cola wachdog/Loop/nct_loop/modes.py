"""Selector 3 modos: módulo ADICIONAL, no cambia el modo del Router automáticamente."""
from .contracts import NCTError
MODES={'manual','semi_auto','nct_continuous'}
def validate_mode(requested:str,*,explicit_user_choice:bool)->str:
    if requested not in MODES:raise NCTError('MODO_NO_RECONOCIDO')
    if requested=='nct_continuous' and not explicit_user_choice:
        raise NCTError('MODO_CONTINUO_REQUIERE_ACTIVACION_EXPLICITA')
    return requested
