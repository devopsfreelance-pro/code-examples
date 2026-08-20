"""Calculadora simple, iteracion 3 (segunda vuelta de kaizen).

Retrospectiva sobre la iteracion 2: las funciones estaban bien
separadas, pero division por cero devolvia 0 en silencio (un bug
disfrazado de feature) y no habia type hints ni validacion de
operacion desconocida. Segunda mejora kaizen: manejo explicito de
errores y tipado, sin agregar complejidad estructural nueva.
"""
from __future__ import annotations


def _add(a: float, b: float) -> float:
    return a + b


def _subtract(a: float, b: float) -> float:
    return a - b


def _multiply(a: float, b: float) -> float:
    return a * b


def _divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("No se puede dividir por cero")
    return a / b


_OPERATIONS = {
    "add": _add,
    "subtract": _subtract,
    "multiply": _multiply,
    "divide": _divide,
}


def calculate(operation: str, a: float, b: float) -> float:
    """Ejecuta la operacion solicitada sobre a y b.

    Lanza ValueError si la operacion no existe o si se intenta
    dividir por cero, en lugar de devolver None o 0 silenciosamente.
    """
    func = _OPERATIONS.get(operation)
    if func is None:
        raise ValueError(f"Operacion desconocida: {operation}")
    return func(a, b)
