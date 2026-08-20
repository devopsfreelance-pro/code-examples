# Autenticación con OAuth2 y OpenID Connect

Ejemplo ejecutable del post: [Guía Completa de Autenticación con OAuth2 y OpenID Connect](https://www.devopsfreelance.pro/blog/posts/autenticacion-con-oauth2-openid-connect/).

## Qué demuestra

El post describe varios flujos de OAuth2/OIDC y menciona a Keycloak como
servidor de autorización auto-hospedado. Este ejemplo levanta un Keycloak
local con un realm ya configurado y ejecuta el **flujo de código de
autorización con PKCE** (el estándar recomendado hoy para SPA y apps
nativas, sección "Flujos modernos para aplicaciones SPA y móviles" del
post):

1. Genera `code_verifier` y `code_challenge` (SHA-256, base64url).
2. Abre el navegador contra el endpoint `/authorize` de Keycloak.
3. Recibe el `authorization code` en un callback local (`http://localhost:8000/callback`).
4. Intercambia el code por `access_token` e `id_token` en el endpoint `/token`, enviando el `code_verifier` para probar que quien completa el flujo es quien lo inició.
5. Decodifica el `id_token` (JWT) y muestra los claims de identidad del usuario (`sub`, `email`, `preferred_username`, etc.).

## Requisitos

- Docker y Docker Compose
- Python 3.8+ (solo librería estándar, sin `pip install`)
- Un navegador disponible en la misma máquina

## Pasos

1. Levantar Keycloak con el realm de demo ya importado:

```bash
docker compose up -d
```

2. Esperar a que el healthcheck esté OK (puede tardar ~30-60s la primera vez):

```bash
docker compose ps
```

3. Ejecutar el script del flujo PKCE:

```bash
python3 oauth_pkce_demo.py
```

4. Se abre el navegador en la pantalla de login de Keycloak. Iniciar sesión con el usuario de prueba:

```
usuario: demo
contraseña: demo123
```

5. Tras el login, Keycloak redirige a `http://localhost:8000/callback`. La terminal muestra el intercambio de tokens automáticamente.

## Salida esperada

```
Abriendo el navegador para autenticarse en Keycloak...
Si no se abre solo, visitá:
http://localhost:8080/realms/demo/protocol/openid-connect/auth?response_type=code&...

Usuario de prueba: demo / demo123

Esperando el callback en http://localhost:8000/callback ...
Authorization code recibido: SGVsbG8gV29y...

Tokens recibidos del servidor de autorización:
  access_token (primeros 24 chars): eyJhbGciOiJSUzI1NiIs...
  id_token (primeros 24 chars):     eyJhbGciOiJSUzI1NiIs...
  expires_in: 60 segundos

Claims del ID Token (identidad del usuario, sin verificar firma aquí):
  sub: 3f7a1c2e-....
  email: demo@example.com
  preferred_username: demo
  name: Demo User
  iat: 1755600000
  exp: 1755600300
```

## Notas

- El script decodifica el `id_token` sin verificar su firma, solo para inspección educativa. En producción hay que validar la firma contra las claves públicas del endpoint JWKS de Keycloak (`/realms/demo/protocol/openid-connect/certs`) y verificar `exp`, `iss` y `aud`.
- El cliente `demo-app` está configurado como público con PKCE obligatorio (`S256`), sin client secret, tal como corresponde a una app que no puede guardar secretos de forma segura.
- Usuario y contraseña de prueba (`demo` / `demo123`) están en `realm-export.json` únicamente para este entorno local descartable. No usar estas credenciales fuera de la demo.
- Consola de administración de Keycloak: `http://localhost:8080` (usuario `admin` / contraseña `admin`, definidos en `docker-compose.yml`, también solo para uso local).

## Limpieza

```bash
docker compose down -v
```
