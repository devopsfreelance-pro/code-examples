"""Aplicacion minima para el ejemplo de CI/CD con GitLab.

Expone una unica funcion pura para poder testearla sin dependencias
externas ni base de datos.
"""


def calcular_descuento(precio: float, porcentaje: int) -> float:
    """Aplica un descuento porcentual a un precio.

    Lanza ValueError si el porcentaje esta fuera de rango [0, 100]
    o si el precio es negativo.
    """
    if precio < 0:
        raise ValueError("El precio no puede ser negativo")
    if not 0 <= porcentaje <= 100:
        raise ValueError("El porcentaje debe estar entre 0 y 100")

    return round(precio * (1 - porcentaje / 100), 2)


if __name__ == "__main__":
    print(calcular_descuento(100, 20))
