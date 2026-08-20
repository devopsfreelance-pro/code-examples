# NoSQL vs SQL: mismo dominio, dos modelos de datos

Post: [NoSQL vs SQL: Guía definitiva para elegir tu base de datos](https://www.devopsfreelance.pro/blog/posts/bases-datos-nosql-vs-sql/)

## Qué demuestra este ejemplo

Levanta **PostgreSQL** (modelo relacional normalizado) y **MongoDB** (modelo de
documentos) con los mismos datos de ejemplo: un cliente con sus pedidos e
items, tal como se describe en el post. Después ejecuta la misma pregunta de
negocio ("dame el pedido completo de un cliente") contra las dos bases para
que se vea en la práctica la diferencia central del artículo:

- En PostgreSQL el dato vive normalizado en 3 tablas (`customers`, `orders`,
  `order_items`) y hace falta un `JOIN` para reconstruir el pedido completo.
- En MongoDB el mismo pedido vive desnormalizado en un único documento por
  cliente, así que se lee con una sola consulta sin `JOIN`.

No demuestra CAP theorem, sharding ni consistencia eventual (eso requeriría
un clúster multi-nodo); se enfoca en el punto que un lector puede verificar
en minutos en su máquina: esquema rígido + JOIN vs esquema flexible +
documento embebido.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, no el binario viejo
  `docker-compose`).
- Puertos libres en el host: `5432` (Postgres) y `27017` (Mongo).

## Pasos para correrlo

```bash
cd bases-datos-nosql-vs-sql

# 1. Levantar ambas bases (Postgres corre sql/init.sql y Mongo corre mongo/seed.js
#    automáticamente al iniciar, vía docker-entrypoint-initdb.d)
docker compose up -d

# 2. Esperar a que ambas pasen el healthcheck
docker compose ps

# 3. Ejecutar la comparación
chmod +x compare.sh
./compare.sh
```

## Salida esperada

```
=== SQL (PostgreSQL) — requiere JOIN entre 3 tablas ===
        email         | order_id | status  |   product_name    | quantity | unit_price
-----------------------+----------+---------+--------------------+----------+------------
 usuario@ejemplo.com   |        1 | shipped | Laptop             |        1 |    1299.99
 usuario@ejemplo.com   |        1 | shipped | Mouse inalambrico  |        2 |      25.50
 usuario@ejemplo.com   |        2 | pending | Teclado mecanico   |        1 |      89.90
(3 rows)

=== NoSQL (MongoDB) — un solo documento, sin JOIN ===
{
  _id: 'usuario@ejemplo.com',
  firstName: 'Juan',
  lastName: 'Perez',
  orders: [
    { orderId: 'ORD-001', status: 'shipped', items: [ ... ] },
    { orderId: 'ORD-002', status: 'pending', items: [ ... ] }
  ]
}
```

## Limpieza

```bash
docker compose down -v
```

## Estructura

```
bases-datos-nosql-vs-sql/
├── docker-compose.yml   # Postgres 16 + MongoDB 7
├── sql/init.sql         # Esquema normalizado + datos de ejemplo (Postgres)
├── mongo/seed.js         # Documentos desnormalizados de ejemplo (Mongo)
└── compare.sh            # Ejecuta la misma pregunta contra ambas bases
```
