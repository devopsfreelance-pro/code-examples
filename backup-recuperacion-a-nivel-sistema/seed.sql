-- Datos de ejemplo para simular una aplicación con datos "críticos"
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    cliente TEXT NOT NULL,
    monto NUMERIC(10, 2) NOT NULL,
    creado_en TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO pedidos (cliente, monto) VALUES
    ('Cliente A', 1500.00),
    ('Cliente B', 2300.50),
    ('Cliente C', 899.99);
