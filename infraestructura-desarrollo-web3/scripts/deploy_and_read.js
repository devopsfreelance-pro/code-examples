// Simula, en local, la pila descrita en el post: un nodo blockchain
// (aqui el nodo en memoria de Hardhat, en produccion seria Infura/Alchemy/
// nodo propio), un contrato inteligente (Token.sol) y una capa de
// interaccion que lee datos on-chain con ethers.js, tal como hace el
// snippet del articulo con ethers.providers.JsonRpcProvider.
const { ethers } = require('hardhat');

async function main() {
  const [deployer, usuario] = await ethers.getSigners();

  console.log('Nodo blockchain local activo (red hardhat, chainId 31337)');
  console.log('Cuenta deployer:', deployer.address);

  // --- Capa de contratos inteligentes ---
  const Token = await ethers.getContractFactory('Token');
  const token = await Token.deploy(1_000_000); // 1,000,000 tokens de supply inicial
  await token.waitForDeployment();
  const contractAddress = await token.getAddress();
  console.log('Contrato Token desplegado en:', contractAddress);

  // --- Transaccion on-chain ---
  const monto = ethers.parseUnits('250', 18);
  const tx = await token.transfer(usuario.address, monto);
  await tx.wait();
  console.log('Transferencia confirmada en el bloque:', tx.blockNumber);

  // --- Lectura de datos on-chain (equivalente a getTokenBalance del post) ---
  async function getTokenBalance(address) {
    const balance = await token.balanceOf(address);
    return ethers.formatUnits(balance, 18);
  }

  const saldoDeployer = await getTokenBalance(deployer.address);
  const saldoUsuario = await getTokenBalance(usuario.address);

  console.log('Saldo deployer:', saldoDeployer, 'DFPD');
  console.log('Saldo usuario :', saldoUsuario, 'DFPD');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
