# Blockchain Testing con Devnets Privadas

Ejemplo de codigo para el post [Blockchain Testing con Devnets Privadas: Guía Definitiva](https://www.devopsfreelance.pro/blog/posts/blockchain-testing-con-devnets-privadas/) del blog DevOps Freelance Pro.

## Que demuestra este ejemplo

El post menciona Hardhat como una de las herramientas para blockchain testing con devnets privadas. Este ejemplo levanta una devnet Ethereum privada local (Hardhat Network) y prueba en ella un smart contract sencillo, `PaymentLedger`, inspirado en el caso de uso de "pagos transfronterizos" que menciona el post:

- Registro de pagos con calculo de un fee de liquidacion (parametro de red ajustable, sin costo real).
- Liquidacion de pagos restringida al owner del contrato.
- Casos limite (monto cero, doble liquidacion, permisos) probados sin arriesgar fondos reales, tal como describe la seccion "Ventajas y Beneficios" del post.

Los tests corren contra una devnet efimera que Hardhat crea y destruye en cada corrida (`npm test`). Ademas se incluye un script de deploy para levantar la misma devnet de forma persistente (`npm run node`) y desplegar el contrato ahi, viendolo "vivo" en `127.0.0.1:8545`.

## Requisitos

- Node.js 18 o superior
- npm

No hace falta Docker, wallets ni tokens reales: Hardhat Network genera 20 cuentas locales precargadas con ETH ficticio.

## Pasos para correrlo

```bash
cd blockchain-testing-con-devnets-privadas
npm install
npm test
```

Salida esperada (resumen):

```
  PaymentLedger (devnet privada)
    ✔ despliega con el owner y el fee configurados
    ✔ registra un pago transfronterizo y calcula el fee de liquidacion
    ✔ rechaza pagos con monto cero (caso limite simulable sin riesgo)
    ✔ solo el owner puede liquidar un pago
    ✔ no permite liquidar dos veces el mismo pago
    ✔ permite ajustar parametros de red/negocio sin costo, como describe el post

  6 passing
```

### Opcional: devnet persistente + deploy manual

Para ver el contrato desplegado en una devnet que queda corriendo (util para conectar un wallet o un script aparte), en dos terminales:

```bash
# Terminal 1: levanta la devnet privada persistente en 127.0.0.1:8545
npm run node

# Terminal 2: despliega el contrato en esa devnet
npm run deploy:local
```

Salida esperada del deploy (la direccion cambia en cada corrida):

```
Desplegando con la cuenta: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
PaymentLedger desplegado en: 0x5FbDB2315678afecb367f032d93F642f64180aa
```

## Estructura

```
blockchain-testing-con-devnets-privadas/
├── contracts/
│   └── PaymentLedger.sol       # Smart contract de ejemplo
├── scripts/
│   └── deploy.js               # Deploy manual contra la devnet persistente
├── test/
│   └── PaymentLedger.test.js   # Tests contra la devnet efimera
├── hardhat.config.js           # Config de la devnet privada (chainId 31337)
└── package.json
```
