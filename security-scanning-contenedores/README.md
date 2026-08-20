# Container Security Scanning con Trivy y Grype

Post: https://www.devopsfreelance.pro/blog/posts/security-scanning-contenedores/

## Que demuestra este ejemplo

Una imagen Docker de ejemplo (`Dockerfile.vulnerable`) con dependencias Node
desactualizadas a proposito (Express 4.16.4, Lodash 4.17.15, Minimist 1.2.0),
escaneada con las dos herramientas que compara el post, Trivy y Grype, sobre
la misma imagen:

- `scan.sh` construye `demo-scan:latest` y la pasa por Trivy (con umbral
  `CRITICAL,HIGH` y un `.trivyignore` que documenta una excepcion aceptada) y
  luego por Grype (con `--fail-on critical`), reproduciendo el flujo de
  "escanear inmediatamente despues de construir la imagen" del post.
- `.trivyignore` muestra como gestionar excepciones de forma explicita, con
  motivo y fecha de revision, en vez de ignorar CVEs silenciosamente.
- `github-actions-example.yml` es la referencia del workflow de CI/CD que
  aparece en el post (no se ejecuta localmente, es solo para consulta).

## Requisitos

- Docker (con el daemon corriendo)
- Conexion a internet la primera vez, para bajar las imagenes
  `aquasec/trivy`, `anchore/grype` y `node:14.17.0-buster-slim`, ademas de
  las bases de datos de vulnerabilidades

No hace falta instalar Trivy ni Grype en el host: ambos corren como
contenedores.

## Pasos para correrlo

```bash
cd security-scanning-contenedores
chmod +x scan.sh
./scan.sh
```

## Salida esperada

Trivy lista primero las CVEs conocidas para Express, Lodash y Minimist
(excluyendo la que quedo documentada en `.trivyignore`):

```
demo-scan:latest (debian 10.x)
===============================
Total: N (HIGH: X, CRITICAL: Y)

┌────────────┬────────────────┬──────────┬─────────┬───────────────────┬───────────────┬──────────────────────┐
│  Library   │ Vulnerability  │ Severity │ Status  │ Installed Version │ Fixed Version │        Title         │
├────────────┼────────────────┼──────────┼─────────┼───────────────────┼───────────────┼──────────────────────┤
│ minimist   │ CVE-2020-7598  │ HIGH     │ fixed   │ 1.2.0              │ 1.2.2         │ Prototype Pollution  │
│ express    │ CVE-2022-24999 │ HIGH     │ fixed   │ 4.16.4             │ 4.17.3        │ ...                  │
└────────────┴────────────────┴──────────┴─────────┴───────────────────┴───────────────┴──────────────────────┘
```

seguido de `Trivy exit code: 1` porque encontro HIGH/CRITICAL sin excepcion.

Despues corre Grype sobre la misma imagen y, si detecta alguna CRITICAL,
termina con `Grype exit code: 1`. El script resume ambos resultados al final
y sale con `exit 1` si cualquiera de los dos escaneres encontro problemas
bloqueantes, igual que el gate de un pipeline CI/CD.

Las CVEs exactas dependen de las bases de datos de Trivy y Grype al momento
de correr el escaneo, por eso no se fija un numero exacto en este README.

## Limpieza

```bash
docker rmi demo-scan:latest
docker volume rm trivy-cache grype-cache
```
