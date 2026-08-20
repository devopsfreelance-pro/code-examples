const http = require('node:http');

const PORT = process.env.PORT || 8080;
const ENVIRONMENT = process.env.APP_ENVIRONMENT || 'development';

function buildHealthPayload() {
  return {
    status: 'ok',
    service: 'ci-cd-github-actions-demo',
    environment: ENVIRONMENT,
  };
}

function createServer() {
  return http.createServer((req, res) => {
    if (req.url === '/health') {
      const payload = buildHealthPayload();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(payload));
      return;
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'not_found' }));
  });
}

if (require.main === module) {
  const server = createServer();
  server.listen(PORT, () => {
    console.log(`Servidor escuchando en http://0.0.0.0:${PORT}`);
  });
}

module.exports = { createServer, buildHealthPayload };
