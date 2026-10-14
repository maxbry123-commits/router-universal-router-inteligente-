def ordenar_sin_duplicados(numeros):
    """Recibe una lista de numeros, elimina duplicados y devuelve
    una nueva lista ordenada de menor a mayor."""
    return sorted(set(numeros))


if __name__ == "__main__":
    ejemplo = [5, 3, 8, 3, 1, 5, 9, 1]
    print(ordenar_sin_duplicados(ejemplo))  # [1, 3, 5, 8, 9]
