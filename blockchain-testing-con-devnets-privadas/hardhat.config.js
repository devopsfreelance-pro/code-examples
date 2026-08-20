require("@nomicfoundation/hardhat-toolbox");

/**
 * Configuracion de la devnet privada.
 *
 * "hardhat" es una devnet efimera que vive solo mientras corren los tests
 * (se usa con `npm test`). "localhost" es la misma devnet pero persistente,
 * levantada aparte con `npm run node` y expuesta en 127.0.0.1:8545 para que
 * otros procesos (scripts, wallets, frontends) se conecten mientras dura.
 */
module.exports = {
  solidity: "0.8.24",
  networks: {
    hardhat: {
      chainId: 31337,
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },
  },
};
