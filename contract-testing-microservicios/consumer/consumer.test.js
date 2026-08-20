const path = require('path');
const { PactV3, MatchersV3 } = require('@pact-foundation/pact');
const { ProductClient } = require('./product-client');

const { like, integer } = MatchersV3;

// Este test representa al equipo de OrderService (consumidor). Al
// ejecutarse, Pact levanta un mock server que se comporta segun la
// interaccion definida y, si el test pasa, escribe el contrato en
// pacts/OrderService-ProductService.json
const provider = new PactV3({
  consumer: 'OrderService',
  provider: 'ProductService',
  dir: path.resolve(__dirname, '..', 'pacts'),
});

describe('Contrato OrderService -> ProductService', () => {
  it('obtiene detalles de un producto existente', async () => {
    provider
      .given('producto 123 existe')
      .uponReceiving('solicitud de detalles de producto')
      .withRequest({
        method: 'GET',
        path: '/products/123',
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: integer(123),
          name: like('Laptop Pro'),
          price: like(1299.99),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const client = new ProductClient(mockServer.url);
      const product = await client.getProduct(123);

      expect(product.name).toBe('Laptop Pro');
      expect(product.id).toBe(123);
    });
  });
});
