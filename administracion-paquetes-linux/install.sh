#!/bin/bash
# Demuestra el flujo tipico de apt en un pipeline de aprovisionamiento:
# actualizar cache, instalar de forma idempotente y no interactiva,
# consultar la politica de versiones (pinning) y bloquear el paquete
# para que no se actualice automaticamente.
set -e

echo "=== 1. Actualizando la cache de paquetes (apt update) ==="
apt update

echo
echo "=== 2. Instalando nginx sin interaccion (DEBIAN_FRONTEND=noninteractive) ==="
DEBIAN_FRONTEND=noninteractive apt install -y nginx

echo
echo "=== 3. Politica de versiones aplicada por el pin en /etc/apt/preferences.d/nginx-pin ==="
apt-cache policy nginx

echo
echo "=== 4. Fijando el paquete (apt-mark hold) para evitar actualizaciones automaticas ==="
apt-mark hold nginx
apt-mark showhold

echo
echo "=== 5. Verificando idempotencia: reinstalar no rompe nada ==="
DEBIAN_FRONTEND=noninteractive apt install -y nginx

echo
echo "=== 6. Version de nginx instalada ==="
dpkg -l | grep nginx
nginx -v

echo
echo "=== Listo. El paquete nginx quedo instalado y en hold (pinned). ==="
