def ordenar_sin_duplicados(numeros):
    """Recibe una lista de números, elimina duplicados y devuelve la lista ordenada de menor a mayor."""
    return sorted(set(numeros))


if __name__ == "__main__":
    ejemplo = [5, 2, 9, 2, 5, 1, 7]
    print(ordenar_sin_duplicados(ejemplo))  # Salida: [1, 2, 5, 7, 9]
