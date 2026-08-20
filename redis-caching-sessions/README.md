# Redis para Caching y Sessions

Ejemplo ejecutable del post: [Redis DevOps: Guía Completa para Caching y Sessions 2026](https://www.devopsfreelance.pro/blog/posts/redis-caching-sessions/).

## Qué demuestra

El post explica dos casos de uso centrales de Redis en DevOps: caching con
patrón cache-aside y TTL, y gestión de sesiones stateless con hashes. Este
ejemplo levanta un Redis local configurado con `maxmemory` y política de
eviction `allkeys-lru` (sección "Optimización de Performance" del post) y
ejecuta un script Python que:

1. **Caching (cache-aside):** simula una consulta lenta a base de datos
   (~250ms), la cachea en Redis con TTL de 60s, y muestra la diferencia de
   tiempo entre un cache miss y un cache hit.
2. **Sesiones:** crea una sesión como hash de Redis (`HSET`) con TTL de 30s,
   y muestra cómo refrescar el TTL ante actividad del usuario sin tocar los
   datos (`EXPIRE`), tal como describe la sección "Gestión de Sesiones con
   Redis".
3. **Pipelining:** compara 100 comandos `SET` ejecutados uno por uno contra
   los mismos 100 comandos agrupados en un pipeline, ilustrando la reducción
   de round-trips de red mencionada en "Optimización de Performance".

## Requisitos

- Docker y Docker Compose
- Nada más: el script Python y sus dependencias corren dentro de un
  contenedor definido en `docker-compose.yml`

## Pasos

1. Levantar Redis y el contenedor con Python + librería `redis`:

```bash
docker compose up -d
```

2. Verificar que Redis esté sano:

```bash
docker compose ps
```

3. Ejecutar el script de demo dentro del contenedor `demo`:

```bash
docker compose exec demo python demo.py
```

4. (Opcional) Inspeccionar las claves creadas directamente con `redis-cli`:

```bash
docker compose exec redis redis-cli KEYS '*'
docker compose exec redis redis-cli CONFIG GET maxmemory-policy
```

5. Cuando termines, bajar el entorno:

```bash
docker compose down
```

## Salida esperada

```
Conectado a Redis en redis:6379
maxmemory-policy configurada: {'maxmemory-policy': 'allkeys-lru'}

=== 1. Caching con patron cache-aside y TTL ===
  [CACHE MISS] product:sku-42 -> consultando DB...
  Tiempo (cache miss): 251.3 ms
  [CACHE HIT] product:sku-42
  Tiempo (cache hit):  1.2 ms
  TTL restante: 60s

=== 2. Gestion de sesiones como hash con TTL deslizante ===
  Sesion creada: session:<uuid> (TTL=30s)
  Datos: {'user_id': '1001', 'email': 'usuario@ejemplo.com', 'role': 'admin'}
  TTL refrescado tras actividad del usuario: 30s

=== 3. Pipelining: agrupar comandos en un solo round-trip ===
  100 SET sin pipeline: 45.8 ms
  100 SET con pipeline: 3.1 ms

Listo. Podes inspeccionar las claves con: docker compose exec redis redis-cli KEYS '*'
```

Los tiempos exactos varían según la máquina, pero la relación entre cache
miss/hit (cientos de veces más lento sin cache) y entre SET individuales/en
pipeline (varias veces más lento sin pipeline) se mantiene siempre.
