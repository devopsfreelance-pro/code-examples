const { expect } = require("chai");
const { ethers } = require("hardhat");

// Estos tests corren contra la devnet privada efimera que Hardhat levanta
// automaticamente (red "hardhat"): cada `npm test` arranca una blockchain
// nueva desde cero, con cuentas precargadas de fondos ficticios y sin costo
// real, tal como describe el post para simular transacciones sin riesgo.
describe("PaymentLedger (devnet privada)", function () {
  let ledger, owner, alice, bob;
  const FEE_BPS = 50; // 0.5%

  beforeEach(async function () {
    [owner, alice, bob] = await ethers.getSigners();

    const PaymentLedger = await ethers.getContractFactory("PaymentLedger");
    ledger = await PaymentLedger.deploy(FEE_BPS);
    await ledger.waitForDeployment();
  });

  it("despliega con el owner y el fee configurados", async function () {
    expect(await ledger.owner()).to.equal(owner.address);
    expect(await ledger.settlementFeeBps()).to.equal(FEE_BPS);
  });

  it("registra un pago transfronterizo y calcula el fee de liquidacion", async function () {
    const amount = ethers.parseEther("1000");

    await expect(ledger.connect(alice).registerPayment(bob.address, amount))
      .to.emit(ledger, "PaymentRegistered")
      .withArgs(0, alice.address, bob.address, amount, (amount * 50n) / 10000n);

    expect(await ledger.paymentsCount()).to.equal(1);
  });

  it("rechaza pagos con monto cero (caso limite simulable sin riesgo)", async function () {
    await expect(
      ledger.connect(alice).registerPayment(bob.address, 0)
    ).to.be.revertedWithCustomError(ledger, "InvalidAmount");
  });

  it("solo el owner puede liquidar un pago", async function () {
    const amount = ethers.parseEther("100");
    await ledger.connect(alice).registerPayment(bob.address, amount);

    await expect(ledger.connect(alice).settlePayment(0)).to.be.revertedWithCustomError(
      ledger,
      "NotOwner"
    );

    await expect(ledger.connect(owner).settlePayment(0)).to.emit(ledger, "PaymentSettled").withArgs(0);
  });

  it("no permite liquidar dos veces el mismo pago", async function () {
    const amount = ethers.parseEther("100");
    await ledger.connect(alice).registerPayment(bob.address, amount);
    await ledger.connect(owner).settlePayment(0);

    await expect(ledger.connect(owner).settlePayment(0)).to.be.revertedWithCustomError(
      ledger,
      "AlreadySettled"
    );
  });

  it("permite ajustar parametros de red/negocio sin costo, como describe el post", async function () {
    await ledger.connect(owner).setSettlementFeeBps(100); // sube el fee a 1%
    expect(await ledger.settlementFeeBps()).to.equal(100);
  });
});
