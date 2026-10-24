def contar_palabras(texto):
    """Devuelve el número de palabras del texto (0 si está vacío)."""
    if not texto:
        return 0
    return len(texto.split())
