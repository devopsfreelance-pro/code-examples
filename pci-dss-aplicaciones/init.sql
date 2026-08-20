-- Esquema de demo: SOLO tokens, nunca PAN (Primary Account Number) real.
-- Ilustra el Requisito 3 de PCI DSS (minimizacion de datos + tokenizacion).
CREATE TABLE IF NOT EXISTS card_tokens (
    id SERIAL PRIMARY KEY,
    customer_email TEXT NOT NULL,
    card_token TEXT NOT NULL UNIQUE,   -- token opaco, no el numero de tarjeta
    last4 CHAR(4) NOT NULL,            -- unico fragmento del PAN que se conserva
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO card_tokens (customer_email, card_token, last4)
VALUES
    ('cliente1@example.com', 'tok_a1b2c3d4e5f6', '4242'),
    ('cliente2@example.com', 'tok_f6e5d4c3b2a1', '1881');
