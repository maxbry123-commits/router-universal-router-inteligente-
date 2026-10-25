def contar_palabras(texto):
    """Cuenta las palabras de un texto separándolas por espacios.

    Ejemplos:
        contar_palabras("hola mundo cruel") -> 3
        contar_palabras("") -> 0
    """
    if not texto:
        return 0
    return len(texto.split())
