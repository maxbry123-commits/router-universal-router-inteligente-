def contar_palabras(texto):
    """Cuenta las palabras de `texto` separadas por espacios en blanco.

    Devuelve la cantidad de palabras; para una cadena vacía (o solo
    espacios) devuelve 0.

    Ejemplo:
        contar_palabras("hola mundo cruel") -> 3
    """
    return len(texto.split())
