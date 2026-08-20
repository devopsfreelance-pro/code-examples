// Load test de ejemplo (basado en el patron del post) contra la API demo.
// Ejecuta un ramp-up hasta 20 usuarios virtuales, sostiene la carga y baja a 0.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

export const options = {
  stages: [
    { duration: '10s', target: 20 },  // ramp-up
    { duration: '20s', target: 20 },  // carga sostenida
    { duration: '10s', target: 0 },   // ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const products = http.get(`${BASE_URL}/products`);
  check(products, {
    'GET /products status is 200': (r) => r.status === 200,
    'GET /products < 500ms': (r) => r.timings.duration < 500,
  });

  const checkout = http.get(`${BASE_URL}/checkout`);
  check(checkout, {
    'GET /checkout status is 200': (r) => r.status === 200,
    'GET /checkout < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
