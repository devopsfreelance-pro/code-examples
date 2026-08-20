const test = require('node:test');
const assert = require('node:assert/strict');
const { buildHealthPayload } = require('./index.js');

test('buildHealthPayload devuelve status ok', () => {
  const payload = buildHealthPayload();
  assert.equal(payload.status, 'ok');
});

test('buildHealthPayload incluye el nombre del servicio', () => {
  const payload = buildHealthPayload();
  assert.equal(payload.service, 'ci-cd-github-actions-demo');
});

test('buildHealthPayload usa APP_ENVIRONMENT cuando está seteada', () => {
  process.env.APP_ENVIRONMENT = 'staging';
  delete require.cache[require.resolve('./index.js')];
  const { buildHealthPayload: buildWithEnv } = require('./index.js');
  const payload = buildWithEnv();
  assert.equal(payload.environment, 'staging');
  delete process.env.APP_ENVIRONMENT;
  delete require.cache[require.resolve('./index.js')];
});

test('buildHealthPayload cae a development por defecto', () => {
  delete process.env.APP_ENVIRONMENT;
  delete require.cache[require.resolve('./index.js')];
  const { buildHealthPayload: buildDefault } = require('./index.js');
  const payload = buildDefault();
  assert.equal(payload.environment, 'development');
});
