"""
Prueba de integración: la cúspide angosta de la pirámide.

A diferencia de test_unit.py, esta prueba SÍ habla con un Redis real
(levantado con docker-compose) a través de StockRepository. Es más lenta
y requiere infraestructura, por eso el pipeline la corre solo después de
que las pruebas unitarias pasan (ver run_pipeline.sh).
"""
import os
import uuid

import pytest

from app import InventoryService, StockRepository, build_redis_client


@pytest.fixture
def repo():
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    client = build_redis_client(host=host, port=port)
    try:
        client.ping()
    except Exception as exc:  # pragma: no cover - mensaje de diagnóstico
        pytest.skip(f"Redis no disponible en {host}:{port} ({exc}); levantalo con docker compose up -d")
    yield StockRepository(client)


def test_restock_y_reserve_persisten_en_redis(repo):
    # SKU único por corrida para no interferir con otras ejecuciones del test.
    sku = f"integration-test-{uuid.uuid4()}"
    service = InventoryService(repo)

    total = service.restock(sku, 20)
    assert total == 20

    # Verifica que el dato realmente quedó escrito en Redis, no solo en memoria.
    assert repo.get(sku) == 20

    restante = service.reserve(sku, 8)
    assert restante == 12
    assert repo.get(sku) == 12
