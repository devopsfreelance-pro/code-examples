"""
Servicio mínimo de inventario.

InventoryService contiene la lógica de negocio pura (sin dependencias externas)
para que pueda probarse con pruebas unitarias rápidas. StockRepository es la
única pieza que habla con Redis, y es lo que las pruebas de integración
ejercitan contra un Redis real.

Esta separación es la que hace posible la pirámide de testing descripta en
el post: base ancha de pruebas unitarias (lógica, sin IO) y una punta angosta
de pruebas de integración (IO real contra Redis).
"""
from __future__ import annotations

import redis


class InsufficientStockError(Exception):
    pass


class InventoryService:
    """Lógica de negocio pura: sin Redis, sin IO, sin red."""

    def __init__(self, repository: "StockRepository"):
        self._repo = repository

    def restock(self, sku: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("quantity debe ser positivo")
        current = self._repo.get(sku)
        new_total = current + quantity
        self._repo.set(sku, new_total)
        return new_total

    def reserve(self, sku: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("quantity debe ser positivo")
        current = self._repo.get(sku)
        if current < quantity:
            raise InsufficientStockError(
                f"stock insuficiente para {sku}: disponible={current}, pedido={quantity}"
            )
        remaining = current - quantity
        self._repo.set(sku, remaining)
        return remaining


class StockRepository:
    """Única capa que toca Redis. Esto es lo que validan las pruebas de integración."""

    def __init__(self, redis_client: "redis.Redis"):
        self._redis = redis_client

    def get(self, sku: str) -> int:
        value = self._redis.get(self._key(sku))
        return int(value) if value is not None else 0

    def set(self, sku: str, quantity: int) -> None:
        self._redis.set(self._key(sku), quantity)

    @staticmethod
    def _key(sku: str) -> str:
        return f"stock:{sku}"


def build_redis_client(host: str = "localhost", port: int = 6379) -> "redis.Redis":
    return redis.Redis(host=host, port=port, db=0, decode_responses=True)
