// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Token ERC-20 minimo, sin dependencias externas, solo para el demo.
/// @dev Implementa a mano las funciones esenciales del estandar ERC-20
///      (balanceOf, transfer) para mantener el ejemplo autocontenido.
contract Token {
    string public name = "DevOps Freelance Demo Token";
    string public symbol = "DFPD";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor(uint256 initialSupply) {
        totalSupply = initialSupply * (10 ** uint256(decimals));
        balanceOf[msg.sender] = totalSupply;
        emit Transfer(address(0), msg.sender, totalSupply);
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "saldo insuficiente");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }
}
