/**
 * API Gateway - punto de entrada unico
 *
 * Responsabilidades de seguridad:
 *  - Autentica al usuario (aqui simulado con un login fijo, en produccion
 *    seria OAuth2/OIDC contra un proveedor de identidad externo).
 *  - Emite un JWT firmado con claims de identidad y roles.
 *  - Reenvia el request al microservicio backend propagando el token.
 *
 * El gateway NO decide autorizacion fina sobre recursos de negocio: eso
 * queda delegado al propio microservicio, que valida el token de forma
 * independiente (principio de "confianza cero" descrito en el post).
 */
const express = require('express');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

// En un entorno real este secreto viene de un gestor de secretos
// (Vault, AWS Secrets Manager, etc.), nunca hardcodeado. Aqui se
// comparte via variable de entorno solo para que el demo sea
// autocontenido y corrible localmente en minutos.
const JWT_SECRET = process.env.JWT_SECRET || 'demo-secret-cambiar-en-produccion';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:4000';

const USERS = {
  ana: { password: 'ana123', id: 'u-ana', roles: ['admin'] },
  luis: { password: 'luis123', id: 'u-luis', roles: ['user'] },
};

// --- Autenticacion: emite JWT tras validar credenciales ---
app.post('/login', (req, res) => {
  const { username, password } = req.body || {};
  const user = USERS[username];

  if (!user || user.password !== password) {
    return res.status(401).json({ error: 'credenciales invalidas' });
  }

  const token = jwt.sign(
    { sub: user.id, username, roles: user.roles },
    JWT_SECRET,
    {
      expiresIn: '5m',
      issuer: 'gateway.demo.local',
      audience: 'orders-service',
    }
  );

  res.json({ access_token: token, token_type: 'Bearer', expires_in: 300 });
});

// --- Proxy hacia el microservicio de pedidos, propagando el JWT ---
app.use('/api/orders', async (req, res) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({ error: 'token no proporcionado' });
  }

  try {
    const url = `${BACKEND_URL}/orders${req.url}`;
    const response = await fetch(url, {
      method: req.method,
      headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : JSON.stringify(req.body),
    });
    const body = await response.json().catch(() => ({}));
    res.status(response.status).json(body);
  } catch (err) {
    res.status(502).json({ error: 'backend no disponible', detail: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`API Gateway escuchando en http://localhost:${PORT}`);
});
