#!/usr/bin/env bash
# Ejecuta la misma pregunta de negocio ("pedido completo de un cliente")
# contra PostgreSQL (modelo normalizado, requiere JOIN) y MongoDB
# (modelo de documento, lectura directa sin JOIN).
set -euo pipefail

CUSTOMER_EMAIL="usuario@ejemplo.com"

echo "=== SQL (PostgreSQL) — requiere JOIN entre 3 tablas ==="
docker compose exec -T postgres psql -U demo -d ecommerce -c "
SELECT c.email, o.order_id, o.status, oi.product_name, oi.quantity, oi.unit_price
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE c.email = '${CUSTOMER_EMAIL}'
ORDER BY o.order_id;
"

echo
echo "=== NoSQL (MongoDB) — un solo documento, sin JOIN ==="
docker compose exec -T mongo mongosh --quiet ecommerce --eval "
printjson(db.customers.findOne({ _id: '${CUSTOMER_EMAIL}' }))
"
