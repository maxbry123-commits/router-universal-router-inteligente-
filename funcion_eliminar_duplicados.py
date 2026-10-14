def eliminar_duplicados_y_ordenar(numeros: list) -> list:
    """
    Recibe una lista de números, elimina duplicados, ordena de menor a mayor y devuelve el resultado.
    
    Args:
        numeros (list): Lista de números que puede contener duplicados.
        
    Returns:
        list: Lista ordenada sin duplicados.
    """
    # Eliminar duplicados usando un conjunto (set), luego convertir a lista y ordenar
    return sorted(set(numeros))


# Ejemplo de uso
if __name__ == "__main__":
    lista_ejemplo = [5, 3, 8, 1, 3, 9, 5, 2, 8, 7]
    resultado = eliminar_duplicados_y_ordenar(lista_ejemplo)
    print(f"Lista original: {lista_ejemplo}")
    print(f"Lista sin duplicados y ordenada: {resultado}")