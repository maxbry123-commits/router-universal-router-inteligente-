def eliminar_duplicados_y_ordenar(numeros: list) -> list:
    """
    Recibe una lista de numeros, elimina duplicados y ordena de menor a mayor.
    
    Args:
        numeros: Lista de numeros (puede contener duplicados)
    
    Returns:
        Lista ordenada sin duplicados
    
    Ejemplo:
        >>> eliminar_duplicados_y_ordenar([3, 1, 4, 1, 5, 9, 2, 6, 5])
        [1, 2, 3, 4, 5, 6, 9]
    """
    # Eliminar duplicados usando set y convertir de vuelta a lista
    sin_duplicados = list(set(numeros))
    
    # Ordenar de menor a mayor
    resultado_ordenado = sorted(sin_duplicados)
    
    return resultado_ordenado


# Ejemplo de uso
if __name__ == "__main__":
    lista_ejemplo = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7]
    resultado = eliminar_duplicados_y_ordenar(lista_ejemplo)
    print(f"Lista original: {lista_ejemplo}")
    print(f"Lista procesada: {resultado}")