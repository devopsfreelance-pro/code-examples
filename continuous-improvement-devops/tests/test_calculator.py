"""Suite de tests compartida entre las 3 iteraciones de sample_app/calculator.py.

Se mantiene igual en las tres corridas a proposito: el objetivo del
demo es medir como cambian complejidad y calidad de codigo cuando el
comportamiento observable (la API publica `calculate`) se mantiene
estable a lo largo de las mejoras kaizen.
"""
from sample_app.calculator import calculate


def test_add():
    assert calculate("add", 2, 3) == 5


def test_subtract():
    assert calculate("subtract", 5, 3) == 2


def test_multiply():
    assert calculate("multiply", 4, 3) == 12


def test_divide():
    assert calculate("divide", 10, 2) == 5
