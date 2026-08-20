# Escaneo de vulnerabilidades en contenedores

Post: https://www.devopsfreelance.pro/blog/posts/escaneo-vulnerabilidades-contenedores/

## Que demuestra este ejemplo

Una imagen Docker de ejemplo (`Dockerfile.vulnerable`) con dependencias Python
desactualizadas a proposito (Flask 1.0, requests 2.20.0, PyYAML 5.1), y un
script (`scan.sh`) que la construye y la escanea con Trivy, exactamente como
describe el post: extraccion de capas, analisis de componentes, comparacion
contra bases de datos de CVEs y generacion de un reporte que hace fallar el
proceso si aparecen vulnerabilidades HIGH o CRITICAL.

Tambien se incluye `gitlab-ci-example.yml` como referencia de como se veria
este mismo escaneo integrado en un pipeline CI/CD (no se ejecuta localmente,
es solo para consulta).

## Requisitos

- Docker (con el daemon corriendo)
- Conexion a internet la primera vez, para bajar la imagen `aquasec/trivy` y
  las bases de datos de vulnerabilidades

No hace falta instalar Trivy en el host: se ejecuta como contenedor.

## Pasos para correrlo

```bash
cd escaneo-vulnerabilidades-contenedores
chmod +x scan.sh
./scan.sh
```

El script hace tres cosas:

1. Construye la imagen `demo-scan:latest` a partir de `Dockerfile.vulnerable`.
2. Corre Trivy contra esa imagen usando el socket de Docker del host (no
   necesita que la imagen este en un registry).
3. Termina con exit code 1 y detalle de CVEs si encuentra vulnerabilidades
   HIGH o CRITICAL con fix disponible; exit code 0 si no encuentra ninguna.

## Salida esperada

Trivy va a listar CVEs conocidas para las librerias desactualizadas del
`Dockerfile.vulnerable`, con una tabla similar a:

```
demo-scan:latest (debian 11.x)
===============================
Total: N (HIGH: X, CRITICAL: Y)

┌─────────────────┬────────────────┬──────────┬─────────┬───────────────────┬───────────────┬─────────────────────────────┐
│     Library      │ Vulnerability  │ Severity │ Status  │ Installed Version │ Fixed Version │            Title             │
├──────────────────┼────────────────┼──────────┼─────────┼───────────────────┼───────────────┼─────────────────────────────┤
│ flask             │ CVE-XXXX-XXXXX │ HIGH     │ fixed   │ 1.0                │ 2.2.5         │ ...                          │
│ pyyaml            │ CVE-XXXX-XXXXX │ CRITICAL │ fixed   │ 5.1                │ 5.4            │ ...                          │
└──────────────────┴────────────────┴──────────┴─────────┴───────────────────┴───────────────┴─────────────────────────────┘
```

y el script termina con:

```
Error: ... vulnerabilities found
```

seguido de `exit 1` (el mismo comportamiento que se busca en un gate de
pipeline CI/CD: bloquear el build si hay CVEs sin corregir).

Las CVEs exactas dependen de la base de datos de Trivy al momento de correr
el escaneo, por eso no se fija un numero exacto en este README.

## Limpieza

```bash
docker rmi demo-scan:latest
docker volume rm trivy-cache
```
