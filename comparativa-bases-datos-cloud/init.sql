-- Habilita la extension que usan RDS y Cloud SQL (PostgreSQL) para
-- rastrear el costo real de cada query ejecutada.
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    status TEXT NOT NULL,
    total_cents INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL
);

-- Datos de ejemplo: 500 clientes y 20000 ordenes, suficiente para que
-- una query sin indice se note en pg_stat_statements.
INSERT INTO customers (name, country)
SELECT
    'Cliente ' || gs,
    (ARRAY['AR', 'CL', 'UY', 'MX', 'ES'])[1 + floor(random() * 5)::int]
FROM generate_series(1, 500) AS gs;

INSERT INTO orders (customer_id, status, total_cents, created_at)
SELECT
    1 + floor(random() * 500)::int,
    (ARRAY['pending', 'paid', 'shipped', 'cancelled'])[1 + floor(random() * 4)::int],
    (random() * 100000)::int,
    now() - (random() * interval '180 days')
FROM generate_series(1, 20000) AS gs;
