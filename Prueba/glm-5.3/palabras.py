def contar_palabras(texto):
    """Cuenta cuántas palabras tiene un texto.

    Una palabra es cualquier secuencia de caracteres separados por espacios
    (uno o más). Si el texto está vacío o solo contiene espacios,
    devuelve 0.

    Args:
        texto (str): El texto cuyo número de palabras se desea contar.

    Returns:
        int: La cantidad de palabras en el texto; 0 si está vacío.
    """
    if not texto or not texto.strip():
        return 0
    return len(texto.split())
