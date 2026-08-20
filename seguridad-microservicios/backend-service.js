/**
 * Microservicio backend (servicio de pedidos)
 *
 * Nunca confia en el gateway: valida el JWT de forma independiente
 * (firma, issuer, audience, expiracion) en cada request, tal como
 * describe el post para el patron de "confianza cero" entre servicios.
 * Luego aplica autorizacion basada en roles sobre el recurso solicitado,
 * equivalente en espiritu a una politica de Open Policy Agent (OPA)
 * pero implementada inline para que el demo no dependa de OPA.
 */
const express = require('express');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

const JWT_SECRET = process.env.JWT_SECRET || 'demo-secret-cambiar-en-produccion';

const ORDERS = {
  '1': { id: '1', owner: 'u-luis', total: 120.5, items: ['teclado'] },
  '2': { id: '2', owner: 'u-ana', total: 899.0, items: ['notebook'] },
};

function authenticateRequest(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'token no proporcionado' });
  }

  jwt.verify(
    token,
    JWT_SECRET,
    { issuer: 'gateway.demo.local', audience: 'orders-service', algorithms: ['HS256'] },
    (err, decoded) => {
      if (err) {
        return res.status(403).json({ error: 'token invalido', detail: err.message });
      }
      req.user = decoded;
      next();
    }
  );
}

// Autorizacion: un admin ve todos los pedidos, un usuario solo el propio.
app.get('/orders/:id', authenticateRequest, (req, res) => {
  const order = ORDERS[req.params.id];

  if (!order) {
    return res.status(404).json({ error: 'pedido no encontrado' });
  }

  const isOwner = order.owner === req.user.sub;
  const isAdmin = req.user.roles?.includes('admin');

  if (!isOwner && !isAdmin) {
    return res.status(403).json({ error: 'no autorizado para ver este pedido' });
  }

  res.json(order);
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`Servicio de pedidos escuchando en http://localhost:${PORT}`);
});
