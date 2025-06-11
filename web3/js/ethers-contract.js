// Ejemplo: Interactuando con un contrato usando ethers.js
import { ethers } from 'ethers';

async function mintNFT() {
  // Conectar a proveedor Ethereum (ej. MetaMask)
  const provider = new ethers.providers.Web3Provider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  const signer = provider.getSigner();
  
  // Direcciones y ABI del contrato
  const contractAddress = '0x1234...';
  const contractABI = [...]; // ABI del contrato
  
  // Crear instancia del contrato
  const nftContract = new ethers.Contract(
    contractAddress,
    contractABI,
    signer
  );
  
  try {
    // Llamar a la función mintNFT
    const tx = await nftContract.mintNFT(await signer.getAddress());
    console.log('Transaction sent:', tx.hash);
    
    // Esperar confirmación
    await tx.wait();
    console.log('NFT minted successfully!');
  } catch (error) {
    console.error('Error minting NFT:', error);
  }
}