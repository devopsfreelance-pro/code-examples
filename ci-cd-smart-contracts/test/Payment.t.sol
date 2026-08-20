// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/Payment.sol";

/// @notice Suite de tests que un job `test` de CI/CD correria en cada push,
///         tal como describe el post en la seccion "Pipeline de CI/CD
///         completo": unit tests, deteccion de reverts y fuzz testing.
contract PaymentTest is Test {
    Payment public payment;
    address public owner;
    address payable public recipient;

    function setUp() public {
        payment = new Payment();
        owner = address(this);
        recipient = payable(makeAddr("recipient"));

        vm.deal(owner, 100 ether);
    }

    function testDepositAndTransfer() public {
        uint256 amount = 1 ether;
        payment.deposit{value: amount}();

        uint256 recipientBalanceBefore = recipient.balance;
        payment.transfer(recipient, amount);

        assertEq(recipient.balance, recipientBalanceBefore + amount);
        assertEq(payment.balances(owner), 0);
    }

    function testRevertOnInsufficientBalance() public {
        payment.deposit{value: 1 ether}();

        vm.expectRevert("Insufficient balance");
        payment.transfer(recipient, 2 ether);
    }

    function testEmitsTransferEvent() public {
        uint256 amount = 0.5 ether;
        payment.deposit{value: amount}();

        vm.expectEmit(true, true, false, true);
        emit Payment.Transfer(owner, recipient, amount);
        payment.transfer(recipient, amount);
    }

    /// @notice Fuzz test: Foundry genera cientos de montos aleatorios para
    ///         buscar edge cases, como menciona el post en la seccion de
    ///         Foundry. Se acota el rango con vm.assume para evitar
    ///         overflows de balance en el propio test.
    function testFuzzDepositAndTransfer(uint96 amount) public {
        vm.assume(amount > 0 && amount <= 100 ether);
        vm.deal(owner, amount);

        payment.deposit{value: amount}();
        payment.transfer(recipient, amount);

        assertEq(recipient.balance, amount);
        assertEq(payment.balances(owner), 0);
    }
}
