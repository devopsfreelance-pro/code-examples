# Migración de datos entre cloud providers con Rclone

Ejemplo ejecutable del post [Guía Completa de Migración entre cloud providers](https://www.devopsfreelance.pro/blog/posts/migracion-entre-cloud-providers/).

## Qué demuestra

El script `demo.sh` reproduce, con contenedores locales, el flujo de la
sección "Herramientas de migración de datos" del post: sincronización de
un bucket de un proveedor a otro con `rclone sync`, seguida de una
verificación de integridad, y luego una sincronización incremental para
minimizar el downtime (el mismo patrón que describe el post para pasar de
AWS S3 a Azure Blob Storage). Concretamente:

1. Levanta dos MinIO (compatibles con la API S3): `origin` simula el bucket
   de AWS S3 y `destination` simula el contenedor de Azure Blob Storage.
2. Crea el bucket de origen y sube archivos de ejemplo (texto y binario).
3. Ejecuta una **sincronización inicial** `rclone sync` origen → destino,
   igual que el ejemplo del post.
4. Corre `rclone check` para verificar que los datos migraron íntegros
   (mismo checksum en ambos lados).
5. Simula que el sistema origen sigue recibiendo escrituras nuevas
   mientras dura la migración (un archivo adicional).
6. Ejecuta una **sincronización incremental**: solo transfiere el archivo
   nuevo, tal como se haría en producción para minimizar la ventana de
   corte descrita en la Fase 4 (migración piloto) y Fase 5 (migración por
   oleadas) del post.
7. Lista el contenido final del destino para confirmar que quedó en
   paridad con el origen.

## Requisitos

- Docker + Docker Compose plugin (`docker compose version`)
- Bash
- No requiere cuentas de AWS ni Azure: `origin` y `destination` son dos
  MinIO locales descartables. Las credenciales (`origin-admin`/`origin-secret`
  y `dest-admin`/`dest-secret`) están definidas en `docker-compose.yml` y
  `rclone.conf` solo para este entorno local, no son secretos reales.

## Cómo correrlo

```bash
chmod +x demo.sh
./demo.sh
```

El script levanta el entorno, corre la migración completa y al finalizar
(o si se interrumpe con Ctrl+C) hace `docker compose down -v` para limpiar
todo automáticamente.

## Salida esperada

Hacia el final vas a ver algo como:

```
==> Verificación de integridad tras la migración (rclone check)
2026/08/20 12:00:00 NOTICE: S3 bucket app-data: 0 differences found
2026/08/20 12:00:00 NOTICE: S3 bucket app-data: 3 matching files

==> Sincronización incremental para minimizar downtime (solo lo nuevo/cambiado)
Transferred:            41 B / 41 B, 100%, 0 B/s, ETA -
Transferred:             1 / 1, 100%

==> Listado final en destino (debe incluir ventas-q3.txt)
   262144 binario.bin
       21 ventas-q1.txt
       21 ventas-q2.txt
       41 ventas-q3.txt

==> Migración completa y verificada. El origen y el destino están en paridad.
```

La sincronización inicial mueve los 3 archivos originales; `rclone check`
confirma "0 differences found"; la sincronización incremental solo
transfiere `ventas-q3.txt` (el archivo nuevo), demostrando que una
migración por oleadas no requiere volver a copiar todo el dataset.

## Archivos

- `docker-compose.yml`: dos MinIO (origen/destino) + un contenedor con
  `rclone` instalado y configurado.
- `rclone.conf`: define los remotes `aws-origin` y `azure-destination`
  apuntando a cada MinIO vía API S3.
- `demo.sh`: orquesta todo el flujo descrito arriba.
