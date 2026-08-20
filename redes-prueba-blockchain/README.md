# Redes de prueba para blockchain

Ejemplo de codigo para el post [Redes de prueba para blockchain: Guía completa DevOps 2025](https://www.devopsfreelance.pro/blog/posts/redes-prueba-blockchain/) del blog DevOps Freelance Pro.

## Que demuestra este ejemplo

El post explica que las devnets locales (Anvil, Hardhat Network) sirven para iterar rápido sin depender de una testnet publica, y que los faucets entregan tokens de prueba sin valor economico con limites por solicitud. Este ejemplo junta ambas ideas:

- Levanta una devnet Ethereum local con **Anvil** (el nodo de desarrollo de Foundry que menciona el post), corriendo en Docker.
- Despliega un smart contract, `TestnetFaucet.sol`, que replica el comportamiento de un faucet real: entrega una cantidad fija de ETH de prueba por solicitud y aplica un cooldown por direccion para evitar abuso.
- El script `deploy.sh` financia el faucet, reclama fondos desde otra cuenta y demuestra que un segundo reclamo inmediato es rechazado por el cooldown, tal como pasaria contra un faucet publico de Sepolia u Holesky (pero aca sin depender de servicios externos ni esperar limites reales).

Todo corre contra ETH sin valor economico, generado localmente por Anvil en las 10 cuentas precargadas que usa por defecto (mnemonic `test test test ... junk`).

## Requisitos

- Docker y Docker Compose (plugin `docker compose`)
- Bash

No hace falta instalar Node, npm, Foundry ni ninguna herramienta de blockchain en tu maquina: todo corre dentro del contenedor oficial `ghcr.io/foundry-rs/foundry`, que incluye `anvil`, `forge` y `cast`.

## Pasos para correrlo

```bash
cd redes-prueba-blockchain

# 1. Levantar la devnet local (Anvil) en background
docker compose up -d

# 2. Compilar, desplegar el faucet y ejecutar el flujo completo
./deploy.sh

# 3. Cuando termines, apagar la devnet
docker compose down
```

## Salida esperada (resumen)

```
==> Esperando a que Anvil este listo en http://127.0.0.1:8545 ...
    Anvil listo.
==> Compilando y desplegando TestnetFaucet.sol ...
Compiling 1 files with Solc 0.8.24
Compiler run successful!
Deployer: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3
==> Faucet desplegado en: 0x5FbDB2315678afecb367f032d93F642f64180aa3
==> Financiando el faucet con 1 ETH de prueba (sin valor real) ...
status               1 (success)
==> Balance del faucet:
1000000000000000000 [1e18]
==> Balance de la cuenta que va a reclamar (antes):
10000.000000000000000000
==> Reclamando fondos del faucet (requestFunds) ...
status               1 (success)
==> Balance de la cuenta que reclamo (despues, debe subir ~0.1 ETH):
10000.099974235317140304
==> Reclamando de nuevo inmediatamente (debe fallar por cooldown activo) ...
    Correcto: el contrato rechazo el segundo reclamo (CooldownActive), igual que un faucet real.
==> Listo. Este flujo demuestra, sobre una devnet local efimera, lo mismo que
    hace un faucet publico de Sepolia/Holesky: entregar fondos de prueba sin
    valor economico y limitar la frecuencia de solicitudes por direccion.
```

La direccion del contrato desplegado cambia en cada corrida porque Anvil reinicia el estado de la devnet cada vez que se levanta el contenedor (`docker compose up -d`).

## Notas

- Las claves privadas usadas en `deploy.sh` (cuentas #0 y #1) son las claves de desarrollo publicas y conocidas que Anvil deriva del mnemonic fijo `test test test test test test test test test test test junk`. Se usan **solo** contra esta devnet local efimera; nunca deben usarse en una testnet publica ni en mainnet.
- El faucet acepta ETH via su funcion `receive()`, igual que como un operador recarga un faucet publico real.

## Estructura

```
redes-prueba-blockchain/
├── contracts/
│   └── TestnetFaucet.sol   # Smart contract que simula un faucet de testnet
├── docker-compose.yml      # Levanta Anvil (devnet local) en Docker
├── deploy.sh                # Despliega el contrato y ejecuta el flujo de faucet
└── foundry.toml             # Configuracion minima de compilacion (Solc 0.8.24)
```
