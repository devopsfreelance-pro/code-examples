const path = require('path');
const axios = require('axios');
const { Verifier } = require('@pact-foundation/pact');
const { createApp } = require('./product-service');

// Este test representa al equipo de ProductService (proveedor). Levanta
// el servicio real en un puerto local y verifica que cumple con el
// contrato generado por el consumidor (consumer/consumer.test.js), leido
// directamente del archivo .json en lugar de un Pact Broker.
describe('Verificacion del proveedor ProductService', () => {
  let server;
  const port = 8081;
  const providerBaseUrl = `http://localhost:${port}`;

  beforeAll((done) => {
    const app = createApp();
    server = app.listen(port, done);
  });

  afterAll((done) => {
    server.close(done);
  });

  it('cumple el contrato publicado por OrderService', () => {
    return new Verifier({
      provider: 'ProductService',
      providerBaseUrl,
      pactUrls: [
        path.resolve(__dirname, '..', 'pacts', 'OrderService-ProductService.json'),
      ],
      stateHandlers: {
        'producto 123 existe': async () => {
          await axios.post(`${providerBaseUrl}/_pact/state`, {
            state: 'producto 123 existe',
          });
          return Promise.resolve();
        },
      },
    }).verifyProvider();
  });
});
