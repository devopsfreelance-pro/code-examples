// Ejemplo: Subiendo archivos a IPFS con JavaScript
import { create } from 'ipfs-http-client';

async function uploadToIPFS(file) {
  const ipfs = create({ url: 'https://ipfs.infura.io:5001/api/v0' });
  
  try {
    const result = await ipfs.add(file);
    console.log('File uploaded to IPFS:', result.path);
    return result.path;
  } catch (error) {
    console.error('Error uploading file to IPFS:', error);
  }
}

// Uso
const fileBuffer = await readFileAsBuffer('image.png');
const ipfsHash = await uploadToIPFS(fileBuffer);