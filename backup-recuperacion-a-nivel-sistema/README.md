# Backup y recuperación a nivel de sistema - Ejemplo ejecutable

Post del blog: [Guía Completa de Backup y recuperación a nivel de sistema](https://www.devopsfreelance.pro/blog/posts/backup-recuperacion-a-nivel-sistema/)

## Qué demuestra este ejemplo

Una versión mínima pero real del flujo de backup/disaster recovery descripto en el
post: backup completo de una base de datos PostgreSQL, comprimido y encriptado con
GPG (AES256), subido a almacenamiento local (equivalente al `S3` del post), con
verificación por checksum y restauración punto a punto ante una pérdida simulada de
datos (RTO/RPO en la práctica, no solo en teoría).

Incluye:

- `docker-compose.yml`: levanta un PostgreSQL local con datos de ejemplo (`seed.sql`).
- `backup.sh`: hace `pg_dump`, comprime con `gzip`, encripta con `gpg --symmetric` y
  aplica una retención simple (últimos 5 backups).
- `restore.sh`: desencripta el backup más reciente (o uno específico) y restaura la
  base de datos, verificando el conteo de filas al final.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- `gpg` instalado en el host (`gpg --version`). En Debian/Ubuntu: `sudo apt install gnupg`.
- Puerto `5432` libre en tu máquina.

No requiere cuentas ni credenciales de AWS: todo corre en local con Docker.

## Pasos para ejecutarlo

```bash
cd backup-recuperacion-a-nivel-sistema

# 1. Levantar PostgreSQL con datos de ejemplo (tabla "pedidos" con 3 filas)
docker compose up -d
# Esperar a que el healthcheck esté "healthy"
docker compose ps

# 2. Dar permisos de ejecución a los scripts
chmod +x backup.sh restore.sh

# 3. (Opcional) definir tu propia passphrase de encriptación
export BACKUP_PASSPHRASE="una-passphrase-segura"

# 4. Ejecutar el backup completo
./backup.sh

# 5. Simular un desastre: borrar los datos
docker exec br-postgres psql -U appuser -d appdb -c "TRUNCATE TABLE pedidos;"
docker exec br-postgres psql -U appuser -d appdb -c "SELECT count(*) FROM pedidos;"
# -> 0 filas: los datos "se perdieron"

# 6. Recuperar desde el backup más reciente
./restore.sh

# 7. Limpiar el entorno cuando termines
docker compose down -v
```

## Salida esperada

Al ejecutar `./backup.sh`:

```
[2026-08-20 10:00:00] Generando dump de appdb...
[2026-08-20 10:00:01] Encriptando backup con GPG (AES256)...
[2026-08-20 10:00:01] Backup completado: .../backups/appdb_20260820_100000.sql.gz.gpg
[2026-08-20 10:00:01] Checksum SHA256: <hash>
[2026-08-20 10:00:01] Tamaño: 4.0K
```

Al ejecutar `./restore.sh` después de truncar la tabla:

```
[2026-08-20 10:05:00] Restaurando desde: .../backups/appdb_20260820_100000.sql.gz.gpg
[2026-08-20 10:05:00] Desencriptando backup...
[2026-08-20 10:05:00] Restaurando datos en appdb...
[2026-08-20 10:05:01] Restauración completada.
[2026-08-20 10:05:01] Verificando datos restaurados...
 pedidos_restaurados
----------------------
                    3
(1 row)
```

Las 3 filas originales (`Cliente A`, `Cliente B`, `Cliente C`) vuelven a estar
disponibles, confirmando que el backup encriptado es restaurable de punta a punta.

## Notas

- `BACKUP_PASSPHRASE` con valor por defecto `cambiar-esta-passphrase` es solo para
  la demo local; en un entorno real usá un secret manager (AWS Secrets Manager,
  Vault, etc.), nunca una passphrase fija en el script.
- El post usa `s3://company-backups` como destino remoto; en este ejemplo los
  backups quedan en `./backups/` para poder correrlo sin cuenta de AWS. El mismo
  script se extiende agregando `aws s3 cp` como se muestra en el post.
