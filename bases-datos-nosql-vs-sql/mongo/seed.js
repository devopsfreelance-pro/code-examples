// Modelo de documento: el mismo dominio (cliente + pedidos + items) pero
// desnormalizado en un unico documento, sin necesidad de JOIN para leerlo.
db = db.getSiblingDB('ecommerce');

db.customers.insertMany([
  {
    _id: 'usuario@ejemplo.com',
    firstName: 'Juan',
    lastName: 'Perez',
    orders: [
      {
        orderId: 'ORD-001',
        status: 'shipped',
        items: [
          { productName: 'Laptop', quantity: 1, unitPrice: 1299.99 },
          { productName: 'Mouse inalambrico', quantity: 2, unitPrice: 25.50 }
        ]
      },
      {
        orderId: 'ORD-002',
        status: 'pending',
        items: [
          { productName: 'Teclado mecanico', quantity: 1, unitPrice: 89.90 }
        ]
      }
    ]
  },
  {
    _id: 'ana.garcia@ejemplo.com',
    firstName: 'Ana',
    lastName: 'Garcia',
    orders: [
      {
        orderId: 'ORD-003',
        status: 'shipped',
        items: [
          { productName: 'Monitor 27 pulgadas', quantity: 1, unitPrice: 320.00 }
        ]
      }
    ]
  }
]);
