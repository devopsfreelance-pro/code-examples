#!/usr/bin/env bash
# Despliega TestnetFaucet.sol en la devnet local (Anvil) levantada por
# docker-compose y simula el flujo de un faucet de testnet: financiar el
# faucet y pedir fondos desde otra cuenta, respetando el cooldown.
#
# No requiere Node/npm/Foundry instalados en el host: todo corre dentro
# del contenedor oficial de Foundry, compartiendo la red del contenedor
# "redes-prueba-anvil" levantado por docker-compose.
set -euo pipefail

IMAGE="ghcr.io/foundry-rs/foundry:latest"
NET="container:redes-prueba-anvil"
RPC_URL="http://127.0.0.1:8545"
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run() {
  docker run --rm --network "$NET" -v "$WORKDIR":/app -w /app "$IMAGE" "$*"
}

echo "==> Esperando a que Anvil este listo en $RPC_URL ..."
ready=0
for i in $(seq 1 30); do
  if run "cast block-number --rpc-url $RPC_URL" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [ "$ready" -ne 1 ]; then
  echo "ERROR: Anvil no respondio a tiempo. Verifica 'docker compose up -d'." >&2
  exit 1
fi
echo "    Anvil listo."

# Cuentas #0 y #1 del mnemonic fijo que usa Anvil por defecto
# ("test test test ... junk"): mismas en toda corrida, ETH sin valor real.
DEPLOYER_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
CLAIMER_KEY="0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
CLAIMER_ADDRESS=$(run "cast wallet address --private-key $CLAIMER_KEY")

echo "==> Compilando y desplegando TestnetFaucet.sol ..."
DEPLOY_OUT=$(run "forge create contracts/TestnetFaucet.sol:TestnetFaucet --rpc-url $RPC_URL --private-key $DEPLOYER_KEY --broadcast")
echo "$DEPLOY_OUT"
FAUCET_ADDRESS=$(echo "$DEPLOY_OUT" | grep -i "Deployed to:" | awk '{print $NF}')

if [ -z "$FAUCET_ADDRESS" ]; then
  echo "ERROR: no se pudo extraer la direccion del contrato desplegado." >&2
  exit 1
fi
echo "==> Faucet desplegado en: $FAUCET_ADDRESS"

echo "==> Financiando el faucet con 1 ETH de prueba (sin valor real) ..."
run "cast send $FAUCET_ADDRESS --rpc-url $RPC_URL --private-key $DEPLOYER_KEY --value 1ether"

echo "==> Balance del faucet:"
run "cast call $FAUCET_ADDRESS 'faucetBalance()(uint256)' --rpc-url $RPC_URL"

echo "==> Balance de la cuenta que va a reclamar (antes):"
run "cast balance $CLAIMER_ADDRESS --rpc-url $RPC_URL --ether"

echo "==> Reclamando fondos del faucet (requestFunds) ..."
run "cast send $FAUCET_ADDRESS 'requestFunds()' --rpc-url $RPC_URL --private-key $CLAIMER_KEY"

echo "==> Balance de la cuenta que reclamo (despues, debe subir ~0.1 ETH):"
run "cast balance $CLAIMER_ADDRESS --rpc-url $RPC_URL --ether"

echo "==> Reclamando de nuevo inmediatamente (debe fallar por cooldown activo) ..."
if run "cast send $FAUCET_ADDRESS 'requestFunds()' --rpc-url $RPC_URL --private-key $CLAIMER_KEY" 2>/tmp/faucet_retry.log; then
  echo "ADVERTENCIA: se esperaba que el segundo reclamo fallara por cooldown." >&2
else
  echo "    Correcto: el contrato rechazo el segundo reclamo (CooldownActive), igual que un faucet real."
fi

echo "==> Listo. Este flujo demuestra, sobre una devnet local efimera, lo mismo que"
echo "    hace un faucet publico de Sepolia/Holesky: entregar fondos de prueba sin"
echo "    valor economico y limitar la frecuencia de solicitudes por direccion."
