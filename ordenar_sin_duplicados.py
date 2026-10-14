def ordenar_sin_duplicados(numeros):
    """Elimina duplicados y devuelve la lista ordenada de menor a mayor."""
    return sorted(set(numeros))


if __name__ == "__main__":
    ejemplo = [5, 2, 9, 2, 5, 1, 7, 1]
    print(ordenar_sin_duplicados(ejemplo))  # [1, 2, 5, 7, 9]
