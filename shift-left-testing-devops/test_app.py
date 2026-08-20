"""
Suite de tests unitarios (base de la pirámide de testing del post).

Corren en milisegundos, sin red ni dependencias externas: el tipo de test
que un desarrollador ejecuta localmente antes de cada commit.
"""

import pytest

from app import aplicar_cupon, calcular_descuento


class TestCalcularDescuento:
    def test_cliente_regular_sin_descuento(self):
        assert calcular_descuento(100.0, "regular") == 100.0

    def test_cliente_premium_10_porciento(self):
        assert calcular_descuento(100.0, "premium") == 90.0

    def test_cliente_vip_20_porciento(self):
        assert calcular_descuento(100.0, "vip") == 80.0

    def test_redondeo_a_dos_decimales(self):
        assert calcular_descuento(99.99, "premium") == 89.99

    def test_precio_negativo_lanza_error(self):
        with pytest.raises(ValueError, match="no puede ser negativo"):
            calcular_descuento(-10.0, "regular")

    def test_tipo_cliente_invalido_lanza_error(self):
        with pytest.raises(ValueError, match="Tipo de cliente inválido"):
            calcular_descuento(100.0, "gold")

    def test_precio_cero_es_valido(self):
        assert calcular_descuento(0.0, "vip") == 0.0


class TestAplicarCupon:
    def test_cupon_50_porciento(self):
        assert aplicar_cupon(100.0, 50) == 50.0

    def test_cupon_0_porciento_no_cambia_precio(self):
        assert aplicar_cupon(100.0, 0) == 100.0

    def test_cupon_100_porciento_deja_precio_en_cero(self):
        assert aplicar_cupon(100.0, 100) == 0.0

    def test_cupon_fuera_de_rango_lanza_error(self):
        with pytest.raises(ValueError, match="entre 0 y 100"):
            aplicar_cupon(100.0, 150)

    def test_cupon_negativo_lanza_error(self):
        with pytest.raises(ValueError, match="entre 0 y 100"):
            aplicar_cupon(100.0, -5)
