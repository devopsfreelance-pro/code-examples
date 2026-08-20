import pytest

from app import calcular_descuento


def test_descuento_veinte_por_ciento():
    assert calcular_descuento(100, 20) == 80.0


def test_descuento_cero_por_ciento():
    assert calcular_descuento(50, 0) == 50.0


def test_descuento_cien_por_ciento():
    assert calcular_descuento(50, 100) == 0.0


def test_precio_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_descuento(-10, 20)


def test_porcentaje_fuera_de_rango_lanza_error():
    with pytest.raises(ValueError):
        calcular_descuento(100, 150)
