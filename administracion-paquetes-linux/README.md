# Administración de paquetes en Linux con apt

Ejemplo de código asociado al post [Apt Package Manager: Guía Completa para Administración Linux](https://www.devopsfreelance.pro/blog/posts/administracion-paquetes-linux/).

## Qué demuestra

Un flujo completo y reproducible de gestión de paquetes con `apt` dentro de un contenedor Ubuntu, tal como se ejecutaría en un pipeline de aprovisionamiento:

1. `apt update` para sincronizar la caché de repositorios.
2. Instalación no interactiva e idempotente de `nginx` con `DEBIAN_FRONTEND=noninteractive`.
3. Consulta de la política de versiones con `apt-cache policy`, mostrando el efecto de un archivo de **pinning** en `/etc/apt/preferences.d/`.
4. Fijado del paquete con `apt-mark hold` para evitar actualizaciones automáticas no controladas (equivalente práctico al pinning en producción).
5. Verificación de idempotencia: reinstalar el mismo paquete no produce cambios ni errores.

## Requisitos

- Docker (o Docker Compose).

## Cómo ejecutarlo

```bash
cd administracion-paquetes-linux
docker compose up --build
```

O sin Compose:

```bash
cd administracion-paquetes-linux
docker build -t apt-demo .
docker run --rm apt-demo
```

## Salida esperada (resumen)

```
=== 1. Actualizando la cache de paquetes (apt update) ===
Get:1 http://archive.ubuntu.com/ubuntu noble InRelease ...
...

=== 2. Instalando nginx sin interaccion (DEBIAN_FRONTEND=noninteractive) ===
...
Setting up nginx (1.24.0-2ubuntu7) ...

=== 3. Politica de versiones aplicada por el pin en /etc/apt/preferences.d/nginx-pin ===
nginx:
  Installed: 1.24.0-2ubuntu7
  Candidate: 1.24.0-2ubuntu7
  Version table:
 *** 1.24.0-2ubuntu7 1001
        100 /var/lib/dpkg/status

=== 4. Fijando el paquete (apt-mark hold) para evitar actualizaciones automaticas ===
nginx set on hold.
nginx

=== 5. Verificando idempotencia: reinstalar no rompe nada ===
nginx is already the newest version (1.24.0-2ubuntu7).

=== 6. Version de nginx instalada ===
ii  nginx  1.24.0-2ubuntu7  all  small, powerful, scalable web/proxy server
nginx version: nginx/1.24.0 (Ubuntu)

=== Listo. El paquete nginx quedo instalado y en hold (pinned). ===
```

El número exacto de versión de `nginx` puede variar según el estado de los repositorios de Ubuntu al momento de ejecutar el ejemplo; lo relevante es observar que:

- `apt-cache policy` refleja la prioridad `1001` definida en `preferences.d/nginx-pin` (el mismo mecanismo descrito en el post para fijar versiones críticas).
- `apt-mark hold` bloquea el paquete frente a `apt upgrade`.
- La segunda instalación es un no-op, ilustrando la idempotencia de `apt install`.

## Archivos

- `Dockerfile` — imagen Ubuntu 24.04 que copia el pin de `nginx` y el script de instalación.
- `install.sh` — script que ejecuta el flujo apt update → install → policy → hold → reinstall.
- `preferences.d/nginx-pin` — archivo de pinning de apt (mismo formato que el del post, `/etc/apt/preferences.d/`).
- `docker-compose.yml` — atajo para build + run.
