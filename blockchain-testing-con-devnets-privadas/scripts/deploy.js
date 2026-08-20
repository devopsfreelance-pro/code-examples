const { ethers } = require("hardhat");

// Despliega PaymentLedger en la devnet persistente levantada con
// `npm run node` (red "localhost"). Sirve para ver el contrato "vivo" en una
// devnet privada, no solo en los tests efimeros.
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Desplegando con la cuenta:", deployer.address);

  const PaymentLedger = await ethers.getContractFactory("PaymentLedger");
  const ledger = await PaymentLedger.deploy(50); // 0.5% fee de liquidacion
  await ledger.waitForDeployment();

  console.log("PaymentLedger desplegado en:", await ledger.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
