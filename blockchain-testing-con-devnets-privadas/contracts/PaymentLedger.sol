// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title PaymentLedger
/// @notice Contrato minimo que simula el caso de uso del post: un registro de
/// pagos transfronterizos que se prueba en una devnet privada antes de tocar
/// una red real, permitiendo ajustar reglas de negocio sin costo ni riesgo.
contract PaymentLedger {
    address public owner;
    uint256 public settlementFeeBps; // fee de liquidacion en basis points (100 = 1%)

    struct Payment {
        address from;
        address to;
        uint256 amount;
        uint256 fee;
        bool settled;
    }

    Payment[] public payments;

    event PaymentRegistered(uint256 indexed id, address indexed from, address indexed to, uint256 amount, uint256 fee);
    event PaymentSettled(uint256 indexed id);

    error NotOwner();
    error InvalidAmount();
    error AlreadySettled();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(uint256 _settlementFeeBps) {
        owner = msg.sender;
        settlementFeeBps = _settlementFeeBps;
    }

    function registerPayment(address to, uint256 amount) external returns (uint256 id) {
        if (amount == 0) revert InvalidAmount();

        uint256 fee = (amount * settlementFeeBps) / 10_000;
        payments.push(Payment({from: msg.sender, to: to, amount: amount, fee: fee, settled: false}));
        id = payments.length - 1;

        emit PaymentRegistered(id, msg.sender, to, amount, fee);
    }

    function settlePayment(uint256 id) external onlyOwner {
        Payment storage p = payments[id];
        if (p.settled) revert AlreadySettled();
        p.settled = true;
        emit PaymentSettled(id);
    }

    function setSettlementFeeBps(uint256 newFeeBps) external onlyOwner {
        settlementFeeBps = newFeeBps;
    }

    function paymentsCount() external view returns (uint256) {
        return payments.length;
    }
}
