function sum(a, b) {
  return a + b;
}

module.exports = { sum };

if (require.main === module) {
  console.log(`2 + 3 = ${sum(2, 3)}`);
}
