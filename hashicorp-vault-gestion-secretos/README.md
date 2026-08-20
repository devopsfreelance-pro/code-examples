# HashiCorp Vault: Secrets Management for DevOps

Runnable example for the post: [HashiCorp Vault: Secrets Management for DevOps Teams](https://www.devopsfreelance.pro/blog/en/posts/hashicorp-vault-guide/)

## What it demonstrates

Spins up a local Vault in dev mode (Docker, no cluster or auto-unseal needed)
and reproduces the post's central concept, least-privilege access policies
(section "Access Policies and Granular Security"):

1. Enables the KV v2 secrets engine at the `secret/` path.
2. Stores an example secret (`secret/myapp/db`, fake database credentials).
3. Loads the `app-policy.hcl` policy (the same one shown in the post), which
   only allows `read`/`list` on `secret/data/myapp/*`.
4. Creates an application token with that policy attached (not the root token).
5. Verifies live that this token **can** read `secret/myapp/db` but
   **cannot** read a secret under a different path (`secret/otraapp/db`) — the
   blast radius stays contained, exactly as the post explains.

It does not include real database dynamic secrets or Kubernetes/AWS
authentication (they require extra infrastructure); the focus is the policy
mechanism, which is the central piece and reproducible in minutes.

## Requirements

- Docker and the `docker compose` plugin (Docker Desktop or Docker Engine + compose plugin).
- No need to install the Vault CLI on your machine: the script runs inside
  the `vault-demo` container itself, which already includes it.

## Files

- `docker-compose.yml`: brings up Vault 1.17 in dev mode (auto-unseal, fixed
  root token `root-demo-token`, for this local demo only) and mounts this
  directory at `/demo` inside the container.
- `app-policy.hcl`: least-privilege policy, identical to the example in the post.
- `setup.sh`: script that runs steps 1 through 5 above against the dev Vault.

## Steps to run it

```bash
# 1. Levantar Vault en modo dev
docker compose up -d

# 2. Esperar a que el healthcheck esté OK (unos segundos)
docker compose ps

# 3. Correr la demo dentro del contenedor
docker compose exec vault sh -c "cd /demo && sh setup.sh"

# 4. (opcional) Explorar la UI de Vault
#    URL:   http://localhost:8200
#    Token: root-demo-token

# 5. Apagar todo
docker compose down -v
```

## Expected output

The script prints, in order: confirmation that Vault is active, the KV v2
engine enabled, the stored secret, the loaded policy, the generated
application token, a successful read of `secret/myapp/db` with the
application token, and a failed (denied) attempt to read `secret/otraapp/db`
with that same token. It ends with a summary:

```
==> Demo completa. Resumen:
 - Secreto propio (secret/myapp/db): acceso permitido
 - Secreto ajeno (secret/otraapp/db): acceso denegado
 - Token root: root-demo-token
 - Token de app (uso limitado): hvs.xxxxxxxxxxxxxxxxxxxxxxxx
```

The application token (`hvs.xxxx...`) is different on every run; the root
token is fixed (`root-demo-token`) because that's how `docker-compose.yml`
defines it, for this local lab only.

## Security note

This setup is exclusively for local learning: Vault runs in dev mode (data
in memory, lost when the container goes down), with a fixed root token in
plain text and no TLS. None of this is production-ready; for that, the post
covers high availability, auto-unseal with KMS, backups, and root token rotation.

---

## 🇪🇸 Versión en español

# HashiCorp Vault: Gestión Segura de Secretos en DevOps

Ejemplo ejecutable del post: [HashiCorp Vault: Gestión Segura de Secretos en DevOps](https://www.devopsfreelance.pro/blog/posts/hashicorp-vault-gestion-secretos/)

## Qué demuestra

Levanta un Vault local en modo dev (Docker, sin necesidad de cluster ni auto-unseal)
y reproduce el concepto central del post, políticas de acceso de mínimo privilegio
(sección "Políticas de Acceso y Seguridad Granular"):

1. Habilita el motor de secretos KV v2 en la ruta `secret/`.
2. Guarda un secreto de ejemplo (`secret/myapp/db`, credenciales ficticias de una base de datos).
3. Carga la política `app-policy.hcl` (la misma que aparece en el post), que solo
   permite `read`/`list` sobre `secret/data/myapp/*`.
4. Crea un token de aplicación con esa política asociada (no el root token).
5. Verifica en vivo que ese token **sí** puede leer `secret/myapp/db` pero
   **no** puede leer un secreto de otra ruta (`secret/otraapp/db`) — el radio de
   explosión queda limitado, tal como explica el post.

No incluye dynamic secrets de base de datos real ni autenticación Kubernetes/AWS
(requieren infraestructura adicional); el foco es el mecanismo de políticas, que es
la pieza central y reproducible en minutos.

## Requisitos

- Docker y el plugin `docker compose` (Docker Desktop o Docker Engine + compose plugin).
- No hace falta instalar el CLI de Vault en tu máquina: el script corre dentro del
  propio contenedor `vault-demo`, que ya lo trae.

## Archivos

- `docker-compose.yml`: levanta Vault 1.17 en modo dev (auto-unseal, root token fijo
  `root-demo-token`, solo para este demo local) y monta este directorio en `/demo`
  dentro del contenedor.
- `app-policy.hcl`: política de mínimo privilegio, idéntica al ejemplo del post.
- `setup.sh`: script que ejecuta los pasos 1 a 5 de arriba contra el Vault dev.

## Pasos para correrlo

```bash
# 1. Levantar Vault en modo dev
docker compose up -d

# 2. Esperar a que el healthcheck esté OK (unos segundos)
docker compose ps

# 3. Correr la demo dentro del contenedor
docker compose exec vault sh -c "cd /demo && sh setup.sh"

# 4. (opcional) Explorar la UI de Vault
#    URL:   http://localhost:8200
#    Token: root-demo-token

# 5. Apagar todo
docker compose down -v
```

## Salida esperada

El script imprime, en orden: confirmación de que Vault está activo, el motor KV v2
habilitado, el secreto guardado, la política cargada, el token de aplicación
generado, una lectura exitosa de `secret/myapp/db` con el token de aplicación, y un
intento fallido (denegado) de leer `secret/otraapp/db` con ese mismo token. Termina
con un resumen:

```
==> Demo completa. Resumen:
 - Secreto propio (secret/myapp/db): acceso permitido
 - Secreto ajeno (secret/otraapp/db): acceso denegado
 - Token root: root-demo-token
 - Token de app (uso limitado): hvs.xxxxxxxxxxxxxxxxxxxxxxxx
```

El token de aplicación (`hvs.xxxx...`) es distinto en cada corrida; el root token
es fijo (`root-demo-token`) porque así lo define `docker-compose.yml` solo para este
laboratorio local.

## Nota de seguridad

Este setup es exclusivamente para aprendizaje local: Vault corre en modo dev (datos
en memoria, se pierden al bajar el contenedor), con un root token fijo en texto
plano y sin TLS. Nada de esto es apto para producción; para eso el post explica
alta disponibilidad, auto-unseal con KMS, backups y rotación del root token.
