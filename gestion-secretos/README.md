# Gestión de secretos: demo con Vault local + Kubernetes Secret

Post relacionado: [Gestión de secretos](https://www.devopsfreelance.pro/blog/posts/gestion-secretos/)

## Qué demuestra este ejemplo

El post explica el concepto central de la gestión de secretos: nunca hardcodear
credenciales, sino recuperarlas de forma programática desde un almacén centralizado
y cifrado. Este ejemplo lo reproduce con dos escenarios mínimos y ejecutables:

1. **Vault en modo dev (Docker)**: se levanta un servidor HashiCorp Vault local,
   se crea un secreto (usuario/contraseña de una base de datos ficticia) y un
   script Python lo recupera vía la API HTTP de Vault, tal como haría una app
   real con AWS Secrets Manager (mismo patrón que el ejemplo `boto3` del post).
2. **Kubernetes Secret nativo**: el manifiesto YAML del post (`Secret` + `Pod`
   consumiendo la variable de entorno vía `secretKeyRef`) llevado a un cluster
   local con `kind`.

## Requisitos

- Docker y Docker Compose (para el escenario Vault)
- `curl` (usado por el script de setup)
- Python 3 (sin dependencias externas, solo librería estándar)
- Opcional, para el escenario Kubernetes: `kind` y `kubectl`

## Escenario 1: Vault local

1. Levantar Vault en modo dev:

   ```bash
   docker compose up -d
   ```

2. Crear el secreto de ejemplo (espera a que Vault esté listo y lo escribe):

   ```bash
   ./setup-vault.sh
   ```

3. Recuperar el secreto de forma programática, como haría la aplicación:

   ```bash
   ./read_db_config.py
   ```

   Salida esperada:

   ```
   Credenciales recuperadas desde Vault (nunca hardcodeadas en el codigo):
     username: app_user
     password: ************ (oculto, 12 caracteres)
   ```

4. También podés inspeccionar el secreto crudo vía la API (solo para ver que
   Vault lo devuelve cifrado en reposo y expuesto solo con el token correcto):

   ```bash
   curl -s --header "X-Vault-Token: root-token-demo" \
     http://127.0.0.1:8200/v1/secret/data/myapp/db | python3 -m json.tool
   ```

5. Limpiar:

   ```bash
   docker compose down -v
   ```

**Nota**: el token `root-token-demo` y la contraseña `S3cr3tP4ss!` son valores
fijos solo para este demo local (Vault en modo dev, sin persistencia). Nunca usar
tokens ni contraseñas fijas en un entorno real; ahí Vault se inicializa con
unseal keys y las credenciales se generan/rotan dinámicamente.

## Escenario 2: Kubernetes Secret

1. Crear un cluster local (si no tenés uno):

   ```bash
   kind create cluster --name secretos-demo
   ```

2. Aplicar el manifiesto:

   ```bash
   kubectl apply -f k8s-manifest-example.yaml
   ```

3. Verificar que el Pod recibió el secreto vía variable de entorno:

   ```bash
   kubectl logs mypod
   ```

   Salida esperada:

   ```
   Usuario recibido via Secret: app_user
   ```

4. Limpiar:

   ```bash
   kubectl delete -f k8s-manifest-example.yaml
   kind delete cluster --name secretos-demo
   ```

## Archivos

- `docker-compose.yml`: servidor Vault en modo dev.
- `setup-vault.sh`: espera a Vault, habilita el motor KV v2 y escribe un secreto de ejemplo.
- `read_db_config.py`: recupera el secreto vía la API HTTP de Vault (solo stdlib).
- `k8s-manifest-example.yaml`: `Secret` + `Pod` de Kubernetes tomados del ejemplo del post.
