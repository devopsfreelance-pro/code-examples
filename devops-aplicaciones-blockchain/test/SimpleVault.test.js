const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("SimpleVault", function () {
  let vault;
  let owner;
  let other;

  beforeEach(async function () {
    [owner, other] = await ethers.getSigners();

    const SimpleVault = await ethers.getContractFactory("SimpleVault");
    vault = await SimpleVault.deploy();
    await vault.waitForDeployment();
  });

  it("Debería permitir depositar ETH y actualizar el balance", async function () {
    const depositAmount = ethers.parseEther("1.0");

    await expect(
      vault.connect(owner).deposit({ value: depositAmount })
    )
      .to.emit(vault, "Deposited")
      .withArgs(owner.address, depositAmount);

    expect(await vault.balanceOf(owner.address)).to.equal(depositAmount);
  });

  it("Debería permitir retirar hasta el balance depositado", async function () {
    const depositAmount = ethers.parseEther("1.0");
    const withdrawAmount = ethers.parseEther("0.4");

    await vault.connect(owner).deposit({ value: depositAmount });

    await expect(
      vault.connect(owner).withdraw(withdrawAmount)
    )
      .to.emit(vault, "Withdrawn")
      .withArgs(owner.address, withdrawAmount);

    expect(await vault.balanceOf(owner.address)).to.equal(
      depositAmount - withdrawAmount
    );
  });

  it("Debería revertir si se intenta retirar más de lo depositado", async function () {
    const depositAmount = ethers.parseEther("0.5");
    const withdrawAmount = ethers.parseEther("1.0");

    await vault.connect(owner).deposit({ value: depositAmount });

    await expect(
      vault.connect(owner).withdraw(withdrawAmount)
    ).to.be.revertedWithCustomError(vault, "InsufficientBalance");
  });

  it("Debería mantener balances separados por cuenta", async function () {
    await vault.connect(owner).deposit({ value: ethers.parseEther("1.0") });
    await vault.connect(other).deposit({ value: ethers.parseEther("2.0") });

    expect(await vault.balanceOf(owner.address)).to.equal(
      ethers.parseEther("1.0")
    );
    expect(await vault.balanceOf(other.address)).to.equal(
      ethers.parseEther("2.0")
    );
  });
});
