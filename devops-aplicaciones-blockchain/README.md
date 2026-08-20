# DevOps para aplicaciones blockchain - Pipeline CI/CD para smart contracts

Post del blog: [7 Claves para Dominar DevOps Blockchain en 2025](https://www.devopsfreelance.pro/blog/posts/devops-aplicaciones-blockchain/)

## Qué demuestra este ejemplo

El post explica cómo aplicar prácticas DevOps (CI/CD, testing automatizado,
linting, análisis estático) al desarrollo de smart contracts. Este ejemplo
reproduce en miniatura ese pipeline de integración continua sobre un contrato
Solidity real:

- `contracts/SimpleVault.sol`: contrato mínimo que permite depositar y retirar
  ETH, siguiendo el patrón *checks-effects-interactions* para evitar
  reentrancy (uno de los riesgos de seguridad que menciona el post).
- `test/SimpleVault.test.js`: suite de tests unitarios con Hardhat + Chai que
  verifica depósitos, retiros, balances separados por cuenta y el revert
  esperado cuando se intenta retirar más de lo depositado.
- `.solhint.json`: reglas de linting para Solidity (equivalente al paso
  `solhint` del workflow del post).
- `.github/workflows/ci.yml`: pipeline de GitHub Actions que instala
  dependencias, lintea, compila y corre los tests en cada push/PR, igual que
  el `smart-contract-ci.yml` descrito en la sección de Integración Continua
  del post.

No incluye despliegue a una red real (mainnet/testnet) ni Terraform del nodo
Ethereum, porque eso requiere cuentas y claves de terceros (Infura/Alchemy,
Etherscan, AWS). El pipeline de test/lint/compile es la parte 100% reproducible
en cualquier máquina sin dependencias pagas: Hardhat levanta una blockchain
local en memoria para correr los tests, no se conecta a ninguna red externa.

## Requisitos

- Node.js 20+ y npm (verificado con Node v20.19.2 / npm 10.8.2)
- Conexión a internet solo para `npm install` (descarga el compilador de
  Solidity la primera vez que se compila)

## Cómo correrlo

```bash
cd devops-aplicaciones-blockchain
npm install
npm run lint
npm run compile
npm test
```

## Salida esperada

`npm run lint` no debe reportar errores (puede mostrar un aviso de nueva
versión de Solhint disponible, se ignora).

`npm run compile`:

```
Downloading compiler 0.8.24
Compiled 1 Solidity file successfully (evm target: paris).
```

(la descarga del compilador solo ocurre la primera vez; en corridas
posteriores usa la caché local).

`npm test`:

```
  SimpleVault
    ✔ Debería permitir depositar ETH y actualizar el balance
    ✔ Debería permitir retirar hasta el balance depositado
    ✔ Debería revertir si se intenta retirar más de lo depositado
    ✔ Debería mantener balances separados por cuenta

  4 passing
```

## Sobre el workflow de GitHub Actions

`.github/workflows/ci.yml` reproduce el mismo flujo (`npm install` → lint →
compile → test) que correría automáticamente en GitHub Actions ante cada
push o pull request. No requiere ningún secreto: a diferencia del workflow
de *despliegue* del post (que sí necesita `DEPLOYER_PRIVATE_KEY`,
`ALCHEMY_API_KEY` y `ETHERSCAN_API_KEY` como GitHub Secrets para desplegar a
una red real), este pipeline de CI corre enteramente contra la red local en
memoria de Hardhat.
