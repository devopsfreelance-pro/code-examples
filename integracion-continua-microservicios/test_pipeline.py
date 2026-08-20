"""
Pruebas del pipeline de CI para payment-service. Reproducen en miniatura las
tres etapas descritas en el post:

  1. unit-test        -> logica de negocio pura, sin red ni base de datos.
                          Corre en milisegundos (payment_service.calculate_fee).
  2. contract-test     -> valida que la respuesta de /pay cumple el contrato
                          publicado (campos y tipos), sin importar los valores.
  3. integration-test  -> golpea el servicio real levantado por docker-compose,
                          que a su vez usa una base de datos Postgres real
                          (no un mock), tal como recomienda el post.

pipeline.sh selecciona que etapa correr con -m unit / -m contract / -m integration.
"""
import os

import pytest
import requests

from payment_service import calculate_fee

SERVICE_URL = os.environ.get("SERVICE_URL", "http://localhost:8080")


# ---------------------------------------------------------------------------
# 1. unit-test: rapida, aislada, sin dependencias externas
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_calculate_fee_standard_amount():
    assert calculate_fee(100.00) == 2.00


@pytest.mark.unit
def test_calculate_fee_applies_minimum():
    assert calculate_fee(1.00) == 0.30


@pytest.mark.unit
def test_calculate_fee_rejects_negative_amount():
    with pytest.raises(ValueError):
        calculate_fee(-10)


# ---------------------------------------------------------------------------
# 2. contract-test: valida el contrato expuesto por /pay
# ---------------------------------------------------------------------------
EXPECTED_CONTRACT = {
    "id": int,
    "customer_id": str,
    "amount": (int, float),
    "fee": (int, float),
    "status": str,
}


@pytest.mark.contract
def test_pay_response_matches_contract():
    response = requests.post(
        f"{SERVICE_URL}/pay",
        json={"amount": 50.00, "customer_id": "contract-check"},
        timeout=5,
    )
    assert response.status_code == 200
    body = response.json()

    for field, expected_type in EXPECTED_CONTRACT.items():
        assert field in body, f"el contrato exige el campo '{field}'"
        assert isinstance(body[field], expected_type), (
            f"'{field}' deberia ser {expected_type}, fue {type(body[field])}"
        )


# ---------------------------------------------------------------------------
# 3. integration-test: contra el servicio + Postgres reales de docker-compose
# ---------------------------------------------------------------------------
@pytest.mark.integration
def test_payment_processing_end_to_end():
    response = requests.post(
        f"{SERVICE_URL}/pay",
        json={"amount": 100.00, "customer_id": "test-123"},
        timeout=5,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["fee"] == 2.00


@pytest.mark.integration
def test_payment_missing_fields_returns_400():
    response = requests.post(f"{SERVICE_URL}/pay", json={"amount": 10}, timeout=5)
    assert response.status_code == 400
