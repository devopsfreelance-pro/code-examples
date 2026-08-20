# SBOM: transparencia de dependencias con Syft y Grype

Ejemplo de código para el post [SBOM: Guía completa de transparencia en dependencias](https://www.devopsfreelance.pro/blog/posts/sbom-transparencia-dependencias/).

## Qué demuestra

Este ejemplo genera un **SBOM** (Software Bill of Materials) en formato CycloneDX
para una pequeña aplicación Node.js de prueba (`sample-app/`), usando **Syft**.
Luego escanea ese SBOM con **Grype** para detectar vulnerabilidades conocidas
(CVEs) en las dependencias declaradas.

La app de ejemplo fija `lodash@4.17.15`, una versión con CVEs públicos conocidos
(por ejemplo prototype pollution), a propósito, para que el escaneo tenga algo
real que reportar.

Ambas herramientas se ejecutan con Docker, sin instalar binarios en la máquina.

## Requisitos

- Docker (con acceso a internet para bajar las imágenes `anchore/syft` y
  `anchore/grype` la primera vez)
- bash

No hace falta Node.js instalado: Syft solo lee `package.json`, no ejecuta `npm install`.

## Pasos para correrlo

```bash
cd sbom-transparencia-dependencias

# 1. Generar el SBOM en formato CycloneDX JSON
./generate-sbom.sh

# 2. Escanear el SBOM contra la base de datos de vulnerabilidades
./scan-sbom.sh
```

## Salida esperada

Del paso 1 (`generate-sbom.sh`):

```
==> Generando SBOM de .../sample-app con Syft (Anchore)
==> SBOM generado en: .../sbom.cyclonedx.json
==> Componentes detectados:
"name": "express"
"name": "lodash"
```

Del paso 2 (`scan-sbom.sh`), una tabla similar a esta (los CVEs y severidades
concretas dependen de la base de datos de vulnerabilidades vigente al momento
de correrlo):

```
==> Escaneando .../sbom.cyclonedx.json con Grype (Anchore)
NAME     INSTALLED  FIXED-IN  TYPE  VULNERABILITY   SEVERITY
lodash   4.17.15    4.17.19   npm   CVE-2020-8203   High
lodash   4.17.15    4.17.21   npm   CVE-2021-23337  High
```

Si no aparece ninguna fila, Grype no encontró vulnerabilidades conocidas en ese
momento contra su base de datos (normal si la BD se actualizó y esas CVEs ya
no aplican a esa combinación paquete/versión).

## Archivos

- `sample-app/package.json` — aplicación de ejemplo con dependencias, una de
  ellas desactualizada a propósito.
- `generate-sbom.sh` — genera `sbom.cyclonedx.json` con Syft vía Docker.
- `scan-sbom.sh` — escanea `sbom.cyclonedx.json` con Grype vía Docker.

`sbom.cyclonedx.json` se genera al correr el script; no está versionado en este
ejemplo.

## Notas

- No se usa ningún servicio pago ni cuenta externa: Syft y Grype corren
  localmente como contenedores públicos de Anchore.
- Para escanear una imagen de contenedor real en vez del directorio de
  ejemplo, cambiá el argumento `dir:/proyecto` en `generate-sbom.sh` por
  `docker:<imagen>:<tag>` (requiere acceso al socket de Docker o exportar la
  imagen primero).
