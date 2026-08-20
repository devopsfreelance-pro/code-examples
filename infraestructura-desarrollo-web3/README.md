# Infraestructura para desarrollo Web3: nodo + contrato inteligente + lectura on-chain

Post relacionado: [Guía Completa de Infraestructura para desarrollo de web3](https://www.devopsfreelance.pro/blog/posts/infraestructura-desarrollo-web3/)

## Qué demuestra

El post describe las capas de una infraestructura web3 (nodo blockchain,
contratos inteligentes, capa de interacción/lectura on-chain) y muestra un
snippet de ejemplo que se conecta a un proveedor de nodos (Alchemy) para leer
el balance de un token ERC-20 con `ethers.js`.

Este ejemplo reproduce esa misma pila, pero 100% local y sin API keys de
terceros:

1. **Nodo blockchain**: la red en memoria que levanta Hardhat (equivalente
   local a Infura/Alchemy/QuickNode, chainId `31337`).
2. **Contrato inteligente**: `contracts/Token.sol`, un token ERC-20 mínimo
   escrito en Solidity, con `balanceOf` y `transfer`.
3. **Capa de interacción on-chain**: `scripts/deploy_and_read.js` despliega
   el contrato, ejecuta una transferencia y lee saldos con `ethers.js`,
   igual que la función `getTokenBalance()` del artículo.

No usa mainnet, testnets públicas ni claves de proveedores (Alchemy/Infura):
todo corre en un nodo Hardhat local que vive solo durante la ejecución del
script.

## Requisitos

- Node.js 18 o superior
- npm

## Cómo correrlo

```bash
cd infraestructura-desarrollo-web3
npm install
npx hardhat run scripts/deploy_and_read.js
```

## Salida esperada

```
Compiled 1 Solidity file successfully (evm target: paris).
Nodo blockchain local activo (red hardhat, chainId 31337)
Cuenta deployer: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Contrato Token desplegado en: 0x5FbDB2315678afecb367f032d93F642f64180aa3
Transferencia confirmada en el bloque: 2
Saldo deployer: 999750.0 DFPD
Saldo usuario : 250.0 DFPD
```

Las direcciones (`0xf39F...`, `0x5FbD...`) son deterministas: Hardhat siempre
arranca sus cuentas de prueba con la misma seed, así que en tu máquina van a
salir exactamente iguales.

## Estructura

```
infraestructura-desarrollo-web3/
├── contracts/
│   └── Token.sol           # Token ERC-20 minimo (capa de contratos inteligentes)
├── scripts/
│   └── deploy_and_read.js  # Deploy + transferencia + lectura on-chain (ethers.js)
├── hardhat.config.js       # Config del nodo local (red "hardhat")
└── package.json
```

## Notas

- `node_modules/`, `artifacts/` y `cache/` se generan al correr `npm install`
  y `npx hardhat run` respectivamente; están en `.gitignore` y no se versionan.
- Para adaptar este ejemplo a un proveedor real (Alchemy, Infura, un nodo
  propio), reemplazá el signer/provider de Hardhat por
  `new ethers.JsonRpcProvider('https://eth-mainnet.alchemyapi.io/v2/<TU_API_KEY>')`
  tal como muestra el snippet del post; ahí sí necesitarías una cuenta y una
  API key del proveedor elegido.
