const axios = require('axios');

/**
 * Cliente del OrderService (consumidor) que consulta al ProductService
 * (proveedor). Este es el codigo "real" del consumidor: el mismo cliente
 * se usa tanto en el test de contrato como en produccion, solo cambia
 * la URL base.
 */
class ProductClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async getProduct(id) {
    const response = await axios.get(`${this.baseUrl}/products/${id}`);
    return response.data;
  }
}

module.exports = { ProductClient };
