const express = require('express');

/**
 * ProductService (proveedor). Implementacion minima con "base de datos"
 * en memoria que se puede poblar via el endpoint /_pact/state, usado por
 * el state handler del test de verificacion del proveedor para simular
 * el estado "producto 123 existe" del contrato.
 */
function createApp() {
  const app = express();
  app.use(express.json());

  let products = {};

  app.post('/_pact/state', (req, res) => {
    const { state } = req.body;

    if (state === 'producto 123 existe') {
      products[123] = { id: 123, name: 'Laptop Pro', price: 1299.99 };
    }

    res.status(200).json({ result: `estado configurado: ${state}` });
  });

  app.get('/products/:id', (req, res) => {
    const product = products[req.params.id];

    if (!product) {
      return res.status(404).json({ error: 'producto no encontrado' });
    }

    res.status(200).json(product);
  });

  return app;
}

if (require.main === module) {
  const app = createApp();
  const port = process.env.PORT || 8080;
  app.listen(port, () => {
    console.log(`ProductService escuchando en http://localhost:${port}`);
  });
}

module.exports = { createApp };
