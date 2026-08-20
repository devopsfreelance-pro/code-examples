-- Esquema normalizado SQL (mismo dominio que el ejemplo del post: e-commerce)
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_name VARCHAR(150) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

INSERT INTO customers (email, first_name, last_name) VALUES
    ('usuario@ejemplo.com', 'Juan', 'Perez'),
    ('ana.garcia@ejemplo.com', 'Ana', 'Garcia');

INSERT INTO orders (customer_id, status) VALUES
    (1, 'shipped'),
    (1, 'pending'),
    (2, 'shipped');

INSERT INTO order_items (order_id, product_name, quantity, unit_price) VALUES
    (1, 'Laptop', 1, 1299.99),
    (1, 'Mouse inalambrico', 2, 25.50),
    (2, 'Teclado mecanico', 1, 89.90),
    (3, 'Monitor 27 pulgadas', 1, 320.00);

-- Consulta que combina 3 tablas para reconstruir el pedido completo de un cliente:
-- este JOIN es el costo estructural del modelo normalizado.
-- (se ejecuta desde compare.sh, se deja documentada aqui como referencia)
-- SELECT c.email, o.order_id, o.status, oi.product_name, oi.quantity, oi.unit_price
-- FROM customers c
-- JOIN orders o ON c.customer_id = o.customer_id
-- JOIN order_items oi ON o.order_id = oi.order_id
-- WHERE c.email = 'usuario@ejemplo.com'
-- ORDER BY o.order_id;
