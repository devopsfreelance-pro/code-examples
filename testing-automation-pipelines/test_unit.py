"""
Pruebas unitarias: base de la pirámide de testing.

No tocan Redis ni ningún IO externo: el StockRepository se reemplaza por un
fake en memoria. Por eso corren en milisegundos y son las primeras en
ejecutarse en el pipeline (ver run_pipeline.sh).
"""
import pytest

from app import InsufficientStockError, InventoryService


class FakeStockRepository:
    """Doble de prueba en memoria: reemplaza a Redis en las pruebas unitarias."""

    def __init__(self):
        self._store: dict[str, int] = {}

    def get(self, sku: str) -> int:
        return self._store.get(sku, 0)

    def set(self, sku: str, quantity: int) -> None:
        self._store[sku] = quantity


@pytest.fixture
def service() -> InventoryService:
    return InventoryService(FakeStockRepository())


def test_restock_incrementa_stock_desde_cero(service: InventoryService):
    total = service.restock("sku-1", 10)
    assert total == 10


def test_restock_acumula_stock_existente(service: InventoryService):
    service.restock("sku-1", 10)
    total = service.restock("sku-1", 5)
    assert total == 15


def test_restock_rechaza_cantidad_no_positiva(service: InventoryService):
    with pytest.raises(ValueError):
        service.restock("sku-1", 0)


def test_reserve_descuenta_stock_disponible(service: InventoryService):
    service.restock("sku-1", 10)
    restante = service.reserve("sku-1", 3)
    assert restante == 7


def test_reserve_falla_si_no_hay_stock_suficiente(service: InventoryService):
    service.restock("sku-1", 2)
    with pytest.raises(InsufficientStockError):
        service.reserve("sku-1", 3)


def test_reserve_rechaza_cantidad_no_positiva(service: InventoryService):
    with pytest.raises(ValueError):
        service.reserve("sku-1", -1)
