# CI/CD para Smart Contracts

Ejemplo de codigo para el post [Guía Completa de CI/CD para smart contracts](https://www.devopsfreelance.pro/blog/posts/ci-cd-smart-contracts/) del blog DevOps Freelance Pro.

## Que demuestra este ejemplo

El post describe un pipeline de CI/CD para smart contracts con Foundry: compilar, correr tests unitarios y de fuzzing, y validar que no haya regresiones de gas antes de mergear. Este ejemplo reproduce ese flujo con un contrato real:

- `src/Payment.sol`: contrato `Payment` con deposito de ETH a un balance interno y transferencia entre cuentas, siguiendo el patron checks-effects-interactions (descuenta el balance antes de la llamada externa) que el post menciona como defensa contra reentrancy.
- `test/Payment.t.sol`: suite de tests Foundry en Solidity (como muestra la seccion "Foundry" del post) con un test de transferencia exitosa, uno de revert por balance insuficiente, uno que verifica el evento emitido, y un **fuzz test** que Foundry corre con cientos de montos aleatorios.
- `.gas-snapshot`: snapshot de consumo de gas de cada test, el mismo mecanismo que el post describe en "Optimización de gas en CI" (`forge snapshot` / `forge snapshot --check`) para detectar regresiones de gas en cada PR.
- `.github/workflows/smart-contract-ci.yml`: pipeline de GitHub Actions con los jobs `compile` -> `test` -> `gas-snapshot`, version simplificada y sin secrets del pipeline completo del post (que ademas incluye analisis estatico con Slither/Mythril y deploy a testnet/mainnet).

## Requisitos

- [Foundry](https://book.getfoundry.sh/getting-started/installation) instalado localmente (`forge`, `cast`), o Docker si preferis no instalar nada.

No hace falta ninguna red real (testnet ni mainnet): todo corre contra la EVM local que Foundry simula en memoria para cada test.

## Pasos para correrlo

### Opcion A: con Foundry instalado

```bash
cd ci-cd-smart-contracts

# Instala forge-std (libreria de testing de Foundry) sin usar git
forge install foundry-rs/forge-std --no-git --no-commit

# Compila los contratos y muestra el tamaño del bytecode (limite EIP-170: 24576 bytes)
forge build --sizes

# Corre la suite completa de tests, incluido el fuzz test
forge test -vv
```

### Opcion B: sin instalar Foundry, con Docker

```bash
cd ci-cd-smart-contracts

docker run --rm -v "$PWD":/app -w /app ghcr.io/foundry-rs/foundry:latest \
  "forge install foundry-rs/forge-std --no-git --no-commit && forge test -vv"
```

## Salida esperada

```
Ran 4 tests for test/Payment.t.sol:PaymentTest
[PASS] testDepositAndTransfer() (gas: 59273)
[PASS] testEmitsTransferEvent() (gas: 62666)
[PASS] testFuzzDepositAndTransfer(uint96) (runs: 256, μ: 62743, ~: 62743)
[PASS] testRevertOnInsufficientBalance() (gas: 41878)
Suite result: ok. 4 passed; 0 failed; 0 skipped; finished in ~10ms
```

Los numeros exactos de gas y el tiempo de ejecucion pueden variar levemente segun la version de `solc` y del CPU, pero los 4 tests deben pasar.

### Verificar que no hay regresiones de gas

```bash
forge snapshot --check --tolerance 5
```

Si algun cambio en `src/Payment.sol` incrementa el gas de un test mas del 5% respecto al `.gas-snapshot` commiteado, este comando falla, igual que lo haria el job `gas-snapshot` del pipeline en `.github/workflows/smart-contract-ci.yml`.

### Usar el pipeline de GitHub Actions

Para probarlo en un repositorio propio: copia `.github/workflows/smart-contract-ci.yml` y las carpetas `src/`, `test/`, `foundry.toml` a un repo en GitHub y hace push. El pipeline instala Foundry con `foundry-rs/foundry-toolchain@v1`, compila, testea y valida el gas snapshot en cada push o pull request a `main`, sin requerir ningun secret (no hace deploy a ninguna red).
