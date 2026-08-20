# Contract Testing para microservicios con Pact

Post: https://www.devopsfreelance.pro/blog/posts/contract-testing-microservicios/

## Qué demuestra este ejemplo

El post describe el flujo de consumer driven contracts con Pact: el
consumidor (`OrderService`) define sus expectativas en un test, eso genera
un archivo de contrato, y el proveedor (`ProductService`) verifica contra
su implementación real que cumple ese contrato, incluyendo el manejo de
estados con `stateHandlers`.

Este ejemplo reproduce ese flujo completo en miniatura, sin Pact Broker
(para no depender de infraestructura extra) y usando el archivo `.json`
del contrato directamente desde disco:

- `consumer/product-client.js`: el cliente HTTP real que usaría
  `OrderService` para hablar con `ProductService`.
- `consumer/consumer.test.js`: test de contrato del consumidor. Al
  correrlo, Pact levanta un mock server, ejecuta el cliente contra ese
  mock y, si todo pasa, escribe el contrato en
  `pacts/OrderService-ProductService.json`.
- `provider/product-service.js`: la implementación real (mínima) de
  `ProductService`, con Express y una "base de datos" en memoria.
- `provider/provider.test.js`: test de verificación del proveedor. Levanta
  `ProductService` de verdad, lee el contrato generado por el consumidor y
  reproduce las solicitudes especificadas contra el servicio real,
  usando un `stateHandler` para preparar el estado `"producto 123 existe"`.

El resultado: si cambiás la respuesta de `ProductService` (por ejemplo
renombrás el campo `name`), la verificación del proveedor falla aunque el
servicio "funcione", porque rompe el contrato que espera `OrderService`.

## Requisitos

- Node.js 18+ y npm
- Sin Docker, sin cuentas externas, sin Pact Broker: todo corre en local
  con archivos

## Cómo correrlo

### 1. Instalar dependencias

```bash
cd contract-testing-microservicios
npm install
```

### 2. Generar el contrato desde el consumidor

```bash
npm run test:consumer
```

Salida esperada (resumida):

```
PASS consumer/consumer.test.js
  Contrato OrderService -> ProductService
    ✓ obtiene detalles de un producto existente

pacts/OrderService-ProductService.json  <- archivo generado
```

Revisá el contrato generado:

```bash
cat pacts/OrderService-ProductService.json
```

Vas a ver un JSON con la interacción `solicitud de detalles de producto`,
el request `GET /products/123` esperado y el response con status 200 y el
body con `id`, `name` y `price`.

### 3. Verificar el contrato desde el proveedor

```bash
npm run test:provider
```

Este comando levanta `ProductService` real en `http://localhost:8081`, lee
el contrato del paso anterior y reproduce la solicitud `GET /products/123`
contra el servicio real, usando el `stateHandler` para poblar el producto
123 antes de la verificación.

Salida esperada (resumida):

```
PASS provider/provider.test.js
  Verificacion del proveedor ProductService
    ✓ cumple el contrato publicado por OrderService
```

### 4. (Opcional) Romper el contrato a propósito

Editá `provider/product-service.js` y cambiá `name: 'Laptop Pro'` por
`nombre: 'Laptop Pro'` (renombrando el campo). Volvé a correr:

```bash
npm run test:provider
```

Ahora la verificación falla, mostrando exactamente qué campo esperado por
el consumidor no está presente en la respuesta real del proveedor. Esto es
lo que en el pipeline de CI/CD bloquearía el despliegue del proveedor
antes de romper la integración en producción.

### 5. (Opcional) Correr el proveedor de forma independiente

```bash
npm run provider:start
curl -X POST http://localhost:8080/_pact/state -H "Content-Type: application/json" -d '{"state":"producto 123 existe"}'
curl http://localhost:8080/products/123
```

## Notas

- En este ejemplo el "broker" es simplemente el archivo
  `pacts/OrderService-ProductService.json` compartido en disco. En un caso
  real ese archivo se publica a un Pact Broker (self-hosted o Pactflow) y
  el proveedor lo descarga desde ahí con `pactBrokerUrl` en vez de
  `pactUrls` apuntando a un path local.
- La carpeta `pacts/` se genera al correr `npm run test:consumer`; no está
  versionada de antemano en este ejemplo.
