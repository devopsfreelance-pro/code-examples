#!/bin/bash
# Entrypoint del contenedor de demo: genera host keys si faltan y arranca sshd
# en primer plano, escuchando en el puerto 2222 (config/sshd_config).
set -euo pipefail

ssh-keygen -A

exec /usr/sbin/sshd -D -e
