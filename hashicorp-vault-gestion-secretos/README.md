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
