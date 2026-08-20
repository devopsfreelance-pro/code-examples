"""Calculadora simple, refactorizada en la iteracion 2.

Retrospectiva: la version 1 concentraba toda la logica en un unico
if/else anidado. Primera mejora kaizen: separar cada operacion en su
propia funcion (reduce complejidad ciclomatica y facilita testear
cada caso por separado).
"""


def _add(a, b):
    return a + b


def _subtract(a, b):
    return a - b


def _multiply(a, b):
    return a * b


def _divide(a, b):
    if b == 0:
        return 0
    return a / b


_OPERATIONS = {
    "add": _add,
    "subtract": _subtract,
    "multiply": _multiply,
    "divide": _divide,
}


def calculate(operation, a, b):
    """Ejecuta la operacion solicitada sobre a y b."""
    func = _OPERATIONS.get(operation)
    if func is None:
        return None
    return func(a, b)
