"""
Demo ejecutable de los dos casos de uso centrales del post:
  1. Caching (patron cache-aside) con TTL y politica de eviction LRU.
  2. Gestion de sesiones como hash de Redis con TTL deslizante.

Tambien muestra pipelining para agrupar comandos en un solo round-trip,
tal como se describe en la seccion "Optimizacion de Performance" del post.
"""

import os
import time
import uuid
import json

import redis

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def slow_db_query(product_id: str) -> dict:
    """Simula una consulta costosa a una base de datos relacional (~250ms)."""
    time.sleep(0.25)
    return {"id": product_id, "name": f"Producto {product_id}", "price": 19.99}


def get_product_cached(product_id: str) -> dict:
    """Patron cache-aside: primero Redis, si falla (cache miss) va a la DB."""
    cache_key = f"product:{product_id}"
    cached = r.get(cache_key)
    if cached is not None:
        print(f"  [CACHE HIT] {cache_key}")
        return json.loads(cached)

    print(f"  [CACHE MISS] {cache_key} -> consultando DB...")
    data = slow_db_query(product_id)
    # TTL de 60s: los datos obsoletos se eliminan solos, sin limpieza manual.
    r.set(cache_key, json.dumps(data), ex=60)
    return data


def demo_caching():
    print("\n=== 1. Caching con patron cache-aside y TTL ===")
    product_id = "sku-42"

    start = time.perf_counter()
    get_product_cached(product_id)
    elapsed_miss = time.perf_counter() - start
    print(f"  Tiempo (cache miss): {elapsed_miss * 1000:.1f} ms")

    start = time.perf_counter()
    get_product_cached(product_id)
    elapsed_hit = time.perf_counter() - start
    print(f"  Tiempo (cache hit):  {elapsed_hit * 1000:.1f} ms")
    print(f"  TTL restante: {r.ttl(f'product:{product_id}')}s")


def demo_sessions():
    print("\n=== 2. Gestion de sesiones como hash con TTL deslizante ===")
    session_id = str(uuid.uuid4())
    session_key = f"session:{session_id}"

    # La sesion se guarda como hash: cada campo es un atributo de sesion.
    r.hset(
        session_key,
        mapping={"user_id": "1001", "email": "usuario@ejemplo.com", "role": "admin"},
    )
    r.expire(session_key, 30)
    print(f"  Sesion creada: {session_key} (TTL=30s)")
    print(f"  Datos: {r.hgetall(session_key)}")

    # Actividad del usuario: se refresca el TTL sin tocar los datos.
    time.sleep(1)
    r.expire(session_key, 30)
    print(f"  TTL refrescado tras actividad del usuario: {r.ttl(session_key)}s")


def demo_pipelining():
    print("\n=== 3. Pipelining: agrupar comandos en un solo round-trip ===")

    start = time.perf_counter()
    for i in range(100):
        r.set(f"pipeline:no:{i}", i)
    elapsed_no_pipeline = time.perf_counter() - start

    start = time.perf_counter()
    pipe = r.pipeline()
    for i in range(100):
        pipe.set(f"pipeline:yes:{i}", i)
    pipe.execute()
    elapsed_pipeline = time.perf_counter() - start

    print(f"  100 SET sin pipeline: {elapsed_no_pipeline * 1000:.1f} ms")
    print(f"  100 SET con pipeline: {elapsed_pipeline * 1000:.1f} ms")

    # Limpieza de las claves de prueba de este bloque.
    keys = r.keys("pipeline:*")
    if keys:
        r.delete(*keys)


if __name__ == "__main__":
    r.ping()
    print(f"Conectado a Redis en {REDIS_HOST}:{REDIS_PORT}")
    print(f"maxmemory-policy configurada: {r.config_get('maxmemory-policy')}")

    demo_caching()
    demo_sessions()
    demo_pipelining()

    print("\nListo. Podes inspeccionar las claves con: docker compose exec redis redis-cli KEYS '*'")
