// scripts/validate-infrastructure.js
// Ejemplo del post: validar configuraciones antes de un despliegue usando
// solo el runtime de Node.js (sin dependencias npm adicionales).
const fs = require('fs/promises');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '..', 'infra-config.json');

const REQUIRED_FIELDS = ['service', 'environment', 'replicas', 'image'];

async function loadConfig(configPath) {
  const raw = await fs.readFile(configPath, 'utf8');
  return JSON.parse(raw);
}

function validateConfig(config) {
  const errors = [];

  for (const field of REQUIRED_FIELDS) {
    if (!(field in config)) {
      errors.push(`Falta el campo obligatorio: "${field}"`);
    }
  }

  if (typeof config.replicas === 'number' && config.replicas < 1) {
    errors.push('"replicas" debe ser mayor o igual a 1');
  }

  if (config.environment && !['staging', 'production'].includes(config.environment)) {
    errors.push(`"environment" invalido: ${config.environment} (usar staging o production)`);
  }

  return errors;
}

async function main() {
  console.log(`Validando configuracion: ${CONFIG_PATH}`);

  const config = await loadConfig(CONFIG_PATH);
  const errors = validateConfig(config);

  if (errors.length > 0) {
    console.error('Configuracion invalida:');
    for (const error of errors) {
      console.error(`  - ${error}`);
    }
    process.exit(1);
  }

  console.log('Configuracion valida:');
  console.log(`  servicio:    ${config.service}`);
  console.log(`  entorno:     ${config.environment}`);
  console.log(`  replicas:    ${config.replicas}`);
  console.log(`  imagen:      ${config.image}`);
  process.exit(0);
}

main().catch((error) => {
  console.error('Error al validar la infraestructura:', error.message);
  process.exit(1);
});
