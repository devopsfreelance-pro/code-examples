"""
Ejemplo mínimo de lógica de negocio para el ejemplo de shift left testing.

Simula el cálculo de descuento de un carrito de una tienda online, el mismo
tipo de función que en el post se menciona como "código nuevo con cobertura
mínima obligatoria del 80%".
"""

TIPOS_CLIENTE_VALIDOS = {"regular", "premium", "vip"}

DESCUENTOS = {
    "regular": 0.0,
    "premium": 0.10,
    "vip": 0.20,
}


def calcular_descuento(precio: float, tipo_cliente: str) -> float:
    """Calcula el precio final aplicando el descuento según el tipo de cliente.

    Lanza ValueError ante datos inválidos: esta validación temprana es lo que
    en el post se llama "primera barrera contra defectos" (tests unitarios
    ejecutados localmente antes del commit).
    """
    if precio < 0:
        raise ValueError("El precio no puede ser negativo")

    if tipo_cliente not in TIPOS_CLIENTE_VALIDOS:
        raise ValueError(f"Tipo de cliente inválido: {tipo_cliente}")

    descuento = DESCUENTOS[tipo_cliente]
    precio_final = precio * (1 - descuento)

    # Redondeo a 2 decimales, como cualquier precio real de e-commerce.
    return round(precio_final, 2)


def aplicar_cupon(precio_final: float, porcentaje_cupon: float) -> float:
    """Aplica un cupón adicional sobre un precio ya calculado.

    porcentaje_cupon debe estar entre 0 y 100.
    """
    if not 0 <= porcentaje_cupon <= 100:
        raise ValueError("El porcentaje de cupón debe estar entre 0 y 100")

    return round(precio_final * (1 - porcentaje_cupon / 100), 2)
