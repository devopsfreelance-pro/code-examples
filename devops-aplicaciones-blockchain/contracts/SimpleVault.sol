// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title SimpleVault
/// @notice Contrato minimo que permite depositar y retirar ETH.
/// @dev Ejemplo didactico para el pipeline de CI/CD del post de DevOps Blockchain.
///      Sigue el patron checks-effects-interactions para evitar reentrancy.
contract SimpleVault {
    mapping(address => uint256) private balances;

    event Deposited(address indexed account, uint256 amount);
    event Withdrawn(address indexed account, uint256 amount);

    error InsufficientBalance(uint256 requested, uint256 available);
    error TransferFailed();

    /// @notice Deposita ETH en la boveda del remitente.
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /// @notice Retira `amount` wei de la boveda del remitente.
    /// @param amount Cantidad en wei a retirar.
    function withdraw(uint256 amount) external {
        uint256 currentBalance = balances[msg.sender];
        if (amount > currentBalance) {
            revert InsufficientBalance(amount, currentBalance);
        }

        // Effects antes de Interactions
        balances[msg.sender] = currentBalance - amount;

        (bool success, ) = msg.sender.call{value: amount}("");
        if (!success) {
            revert TransferFailed();
        }

        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Devuelve el balance depositado por una cuenta.
    function balanceOf(address account) external view returns (uint256) {
        return balances[account];
    }
}
