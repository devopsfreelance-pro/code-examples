// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Payment
/// @notice Contrato minimo usado como caso de estudio en el post sobre
///         CI/CD para smart contracts. Cada cuenta deposita ETH y luego
///         puede transferir desde su balance interno hacia otra cuenta.
///         Sirve para ejercitar en el pipeline de CI/CD lo que el post
///         describe: tests unitarios, fuzz testing y analisis estatico
///         sobre un flujo de fondos real (deposito -> transferencia).
contract Payment {
    mapping(address => uint256) public balances;

    event Deposit(address indexed account, uint256 amount);
    event Transfer(address indexed from, address indexed to, uint256 amount);

    /// @notice Deposita ETH en el balance interno del emisor.
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /// @notice Transfiere `amount` desde el balance interno del emisor
    ///         hacia `recipient`. Sigue el patron checks-effects-interactions
    ///         para prevenir reentrancy: primero descuenta el balance,
    ///         recien despues hace la llamada externa.
    function transfer(address payable recipient, uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;

        (bool success,) = recipient.call{value: amount}("");
        require(success, "Transfer failed");

        emit Transfer(msg.sender, recipient, amount);
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
}
