// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title TestnetFaucet
/// @notice Simula el comportamiento de un faucet de testnet (como los que menciona
/// el post para Sepolia/Holesky): entrega una cantidad fija de "ETH de prueba" por
/// solicitud y aplica un cooldown por direccion para evitar abuso, igual que un
/// faucet real. El contrato se financia solo con ETH de la devnet local (sin
/// valor economico), nunca con fondos reales.
contract TestnetFaucet {
    address public owner;
    uint256 public dripAmount = 0.1 ether;
    uint256 public cooldown = 60 seconds;

    mapping(address => uint256) public lastClaim;

    event Funded(address indexed from, uint256 amount);
    event Dripped(address indexed to, uint256 amount);

    error CooldownActive(uint256 secondsRemaining);
    error EmptyFaucet();
    error NotOwner();

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    /// @notice Cualquiera puede recargar el faucet, igual que operadores
    /// de infraestructura recargan faucets publicos de testnet.
    receive() external payable {
        emit Funded(msg.sender, msg.value);
    }

    /// @notice Solicita ETH de prueba. Respeta el cooldown por direccion.
    function requestFunds() external {
        uint256 nextAvailable = lastClaim[msg.sender] + cooldown;
        if (lastClaim[msg.sender] != 0 && block.timestamp < nextAvailable) {
            revert CooldownActive(nextAvailable - block.timestamp);
        }
        if (address(this).balance < dripAmount) revert EmptyFaucet();

        lastClaim[msg.sender] = block.timestamp;
        (bool ok, ) = msg.sender.call{value: dripAmount}("");
        require(ok, "transferencia fallida");

        emit Dripped(msg.sender, dripAmount);
    }

    /// @notice Permite ajustar el monto entregado, tal como un equipo DevOps
    /// ajustaria parametros de un faucet propio para pruebas de carga.
    function setDripAmount(uint256 newAmount) external onlyOwner {
        dripAmount = newAmount;
    }

    function faucetBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
