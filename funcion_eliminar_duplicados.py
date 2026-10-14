def eliminar_duplicados_y_ordenar(numeros: list) -> list:
    """
    Recibe una lista de numeros, elimina los duplicados y los ordena de menor a mayor.
    
    Parametros:
        numeros (list): Lista de numeros que puede contener duplicados.
    
    Retorna:
        list: Lista de numeros sin duplicados, ordenada de menor a mayor.
    
    Explicacion breve:
        1. Se convierte la lista a un conjunto (set) para eliminar automaticamente los duplicados,
           ya que los conjuntos solo almacenan elementos unicos.
        2. Se convierte el conjunto de vuelta a una lista.
        3. Se ordena la lista usando la funcion sorted(), que devuelve una nueva lista ordenada
           de menor a mayor.
    """
    # Eliminar duplicados convirtiendo a set y luego a list
    numeros_unicos = list(set(numeros))
    
    # Ordenar de menor a mayor
    resultado_ordenado = sorted(numeros_unicos)
    
    return resultado_ordenado


# Ejemplo de uso
if __name__ == "__main__":
    lista_ejemplo = [5, 3, 8, 1, 3, 5, 9, 2, 8, 1]
    print(f"Lista original: {lista_ejemplo}")
    resultado = eliminar_duplicados_y_ordenar(lista_ejemplo)
    print(f"Lista sin duplicados y ordenada: {resultado}")
