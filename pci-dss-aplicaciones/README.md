# PCI DSS en aplicaciones: secure coding en la práctica

Post: [PCI DSS: Guía Completa para Aplicaciones Seguras 2026](https://www.devopsfreelance.pro/blog/posts/pci-dss-aplicaciones/)

## Qué demuestra este ejemplo

Una mini API (Flask + PostgreSQL) que ilustra tres controles concretos que el
post menciona como núcleo del cumplimiento de PCI DSS a nivel de código:

- **Requisito 3 (protección de datos del titular de la tarjeta)**: la base
  de datos solo guarda un token opaco (`card_token`) y los últimos 4 dígitos
  (`last4`). El PAN (número de tarjeta) completo nunca se almacena.
- **Requisito 2 / 6.2 (sin credenciales hardcodeadas)**: la contraseña de la
  base de datos se lee desde un *secret file* montado por Docker
  (`DB_PASSWORD_FILE`), nunca desde el código fuente ni desde una variable
  de entorno en texto plano dentro de la imagen.
- **Requisito 6.2 (prevención de SQL injection)**: la consulta que busca un
  token por email usa una sentencia parametrizada (`%s` + tupla de
  parámetros vía `psycopg2`). El endpoint
  `/token-lookup-vulnerable-example` muestra, solo a modo educativo y sin
  ejecutar ninguna query, cómo se ve la versión insegura por concatenación
  de strings que el requisito prohíbe.
- **Requisito 10 (logging de accesos)**: cada consulta a datos del titular
  de la tarjeta queda registrada en el log de la app (sin loguear el dato
  sensible).

Incluye además `scan_hardcoded_creds.sh`, un mini-SAST en bash que busca
patrones de credenciales hardcodeadas (passwords, API keys, claves AWS,
claves privadas) en el código fuente, como los que un pipeline de CI/CD
correría antes de cada merge.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puerto `8080` libre en tu máquina

## Cómo correrlo

1. Entrar al directorio del ejemplo:

   ```bash
   cd pci-dss-aplicaciones
   ```

2. El repo ya incluye `secrets/db_password.txt` con el valor de ejemplo
   `change-me-local-dev-only`, para que el ejemplo funcione out-of-the-box
   (incluido en CI). Si querés regenerarlo o cambiar el valor local:

   ```bash
   mkdir -p secrets
   echo "change-me-local-dev-only" > secrets/db_password.txt
   ```

   En un entorno real este archivo NUNCA se commitea: el valor sale de AWS
   Secrets Manager, Vault o un secreto de Kubernetes, como menciona el post.

3. Levantar la base de datos y la API:

   ```bash
   docker compose up --build -d
   ```

4. Esperar a que la API esté sana y probar el endpoint seguro:

   ```bash
   curl -s http://localhost:8080/health
   curl -s "http://localhost:8080/token-lookup?email=cliente1@example.com"
   ```

   Salida esperada:

   ```json
   {"status":"ok"}
   {"card_token":"tok_a1b2c3d4e5f6","last4":"4242"}
   ```

5. Probar la validación de entrada (Requisito 6.2) con un email inválido:

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8080/token-lookup?email=no-es-un-email"
   ```

   Salida esperada: `400`

6. Ver el log de acceso a datos del titular de la tarjeta (Requisito 10):

   ```bash
   docker compose logs app | grep cardholder_data_access
   ```

   Salida esperada (ejemplo):

   ```
   pci-demo-app  | 2026-08-19 ... level=INFO event=cardholder_data_access email=cliente1@example.com found=True
   ```

7. Ver el endpoint educativo que muestra la consulta insegura (no se
   ejecuta contra la base):

   ```bash
   curl -s "http://localhost:8080/token-lookup-vulnerable-example?email=test"
   ```

   Salida esperada:

   ```json
   {"unsafe_query":"SELECT card_token FROM card_tokens WHERE customer_email = 'test'","warning":"ejemplo educativo, no ejecutado"}
   ```

8. Correr el mini-SAST de credenciales hardcodeadas sobre el propio
   código del ejemplo:

   ```bash
   chmod +x scan_hardcoded_creds.sh
   ./scan_hardcoded_creds.sh .
   ```

   Salida esperada: `RESULTADO: sin coincidencias. OK.` (exit code 0)

9. Apagar todo:

   ```bash
   docker compose down -v
   ```

## Notas

- `secrets/db_password.txt` es un valor de ejemplo para desarrollo local
  únicamente (`change-me-local-dev-only`), incluido en el repo para que el
  demo corra sin pasos manuales. Nunca commitear secretos reales: en un
  proyecto real ese archivo va en `.gitignore` y el valor sale de un
  gestor de secretos.
- Este ejemplo es deliberadamente mínimo: no reemplaza una implementación
  completa de PCI DSS (falta TLS, WAF, MFA, SIEM, etc.), solo ilustra el
  patrón de secure coding a nivel de aplicación que describe el post.
