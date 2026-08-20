# Seguridad en microservicios: demo de autenticacion JWT zero-trust

Post: https://www.devopsfreelance.pro/blog/posts/seguridad-microservicios/

## Que demuestra este ejemplo

Un API Gateway y un microservicio backend independientes, comunicandose
mediante JWT, ilustrando dos ideas centrales del post:

- **API Gateway como punto de entrada unificado**: autentica al usuario
  (`POST /login`), emite un JWT firmado con `roles` y reenvia las
  solicitudes al servicio backend propagando el token en el header
  `Authorization`.
- **Confianza cero entre servicios**: el microservicio backend (servicio
  de pedidos) NO confia en que el trafico que recibe viene realmente del
  gateway. Valida el JWT de forma independiente en cada request (firma,
  `issuer`, `audience`, expiracion) y aplica autorizacion basada en rol
  y propiedad del recurso, en el mismo espiritu que una politica de
  Open Policy Agent (OPA) descrita en el post, aunque aqui implementada
  inline para no depender de infraestructura extra.

El script `test.sh` ejecuta el flujo completo: login, acceso autorizado,
acceso denegado por falta de permisos, bypass del gateway (rechazado) y
token manipulado (rechazado).

## Requisitos

- Node.js 18 o superior (usa el `fetch` global de Node, sin dependencias
  extra para el proxy)
- npm
- curl y python3 (solo los usa `test.sh` para parsear el JSON de la
  respuesta de login; no son necesarios para correr el gateway/backend)

No requiere Docker, Kubernetes ni cuentas en la nube: todo corre local.

## Pasos para correrlo

1. Instalar dependencias:

   ```bash
   cd seguridad-microservicios
   npm install
   ```

2. En una terminal, levantar el microservicio backend (puerto 4000):

   ```bash
   npm run backend
   ```

3. En otra terminal, levantar el API Gateway (puerto 3000):

   ```bash
   npm run gateway
   ```

4. En una tercera terminal, correr el script de pruebas:

   ```bash
   ./test.sh
   ```

## Salida esperada

```
== 1. Login como luis (rol user) ==
Token obtenido (truncado): eyJhbGciOiJIUzI1NiI...

== 2. luis consulta su propio pedido (1) -> esperado 200 ==
HTTP 200

== 3. luis intenta ver el pedido de ana (2) -> esperado 403 ==
HTTP 403

== 4. Login como ana (rol admin) y ver pedido de luis (1) -> esperado 200 ==
HTTP 200

== 5. Request directo al backend SIN token -> esperado 401 (el servicio no confia en el gateway) ==
HTTP 401

== 6. Request con token manipulado -> esperado 403 ==
HTTP 403

Listo.
```

## Usuarios de prueba

| usuario | password | rol   |
|---------|----------|-------|
| ana     | ana123   | admin |
| luis    | luis123  | user  |

Estas credenciales y el `JWT_SECRET` por defecto (`demo-secret-cambiar-en-produccion`)
son solo para este demo local. En produccion las credenciales viven en un
proveedor de identidad (OAuth2/OIDC) y el secreto de firma en un gestor
de secretos (Vault, AWS Secrets Manager, etc.), tal como se explica en
el post original.

## Relacion con el post

Este ejemplo cubre en codigo ejecutable los patrones "API Gateway",
"Tokens JWT para propagacion de identidad" y "Autorizacion basada en
politicas" de la guia. No implementa mTLS, service mesh ni Vault: esos
requieren infraestructura adicional (Istio/Linkerd, un cluster Vault) y
quedan fuera del alcance de un mini-ejemplo corrible en minutos.
