// scripts/health-check.js
// Ejemplo del post: health check asincrono no bloqueante con el modulo http nativo.
const http = require('http');

const url = process.env.HEALTH_URL || 'http://localhost:8080/';
const timeoutMs = Number(process.env.HEALTH_TIMEOUT_MS || 5000);

function checkEndpoint(target) {
  const request = http.get(target, { timeout: timeoutMs }, (response) => {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      console.log(`Servicio saludable (HTTP ${response.statusCode}) - ${target}`);
      response.resume();
      process.exit(0);
    } else {
      console.error(`Servicio degradado (HTTP ${response.statusCode}) - ${target}`);
      response.resume();
      process.exit(1);
    }
  });

  request.on('timeout', () => {
    console.error(`Tiempo de espera agotado tras ${timeoutMs} ms - ${target}`);
    request.destroy();
    process.exit(1);
  });

  request.on('error', (error) => {
    console.error('Error al contactar el servicio:', error.message);
    process.exit(1);
  });
}

checkEndpoint(url);
