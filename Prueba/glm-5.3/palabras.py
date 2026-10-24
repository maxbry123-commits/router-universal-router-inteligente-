def contar_palabras(texto):
    """Cuenta la cantidad de palabras en un texto.

    Args:
        texto: Cadena de texto a evaluar.

    Returns:
        int: 0 si la cadena es vacía o solo tiene espacios;
        en caso contrario, la cantidad de palabras separadas
        por espacios en blanco (ej. "hola mundo cruel" -> 3).
    """
    if not texto or not texto.strip():
        return 0
    return len(texto.split())
