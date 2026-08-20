#!/bin/bash
# Demo de los comandos de SELinux del post "Configuracion de Firewalls y
# SELinux". Corre dentro del contenedor firewall-selinux-lab.
#
# IMPORTANTE: SELinux es una caracteristica del KERNEL, no del contenedor.
# Docker Desktop / la mayoria de los hosts Ubuntu no traen el kernel
# compilado con soporte SELinux, asi que dentro de este contenedor vas a ver
# "SELinux status: disabled" aunque el paquete policycoreutils este
# instalado. Este script detecta esa situacion y lo explica en vez de
# fallar. Los mismos comandos, corridos en un host real Rocky/RHEL/Fedora
# (o en una VM con ese kernel), si muestran contextos y politicas reales.
set -euo pipefail

log() { echo; echo "== $* =="; }

log "1. Estado de SELinux en este kernel"
if [ -e /sys/fs/selinux ]; then
    getenforce
    sestatus
else
    echo "/sys/fs/selinux no existe: el kernel de este host/contenedor no"
    echo "tiene SELinux compilado o habilitado. getenforce/sestatus abajo"
    echo "muestran el estado real, que sera 'disabled':"
    getenforce || true
    sestatus || true
fi

log "2. Contexto de seguridad de archivos servidos por httpd (columna final de ls -Z)"
mkdir -p /var/www/html
echo "<h1>demo</h1>" > /var/www/html/index.html
ls -Z /var/www/html/ || echo "ls -Z no devuelve contexto (SELinux deshabilitado en este kernel)"

log "3. Contexto de seguridad de procesos (columna final de ps -Z)"
httpd -k start
sleep 1
ps -Z -C httpd || echo "ps -Z no devuelve contexto (SELinux deshabilitado en este kernel)"
httpd -k stop

log "4. Booleanos relacionados con httpd (requieren policy cargada)"
getsebool -a 2>/dev/null | grep httpd || echo "getsebool: sin policy SELinux cargada en este kernel, nada que listar"

log "5. Comandos de referencia para un host con SELinux enforcing real (Rocky/RHEL/Fedora)"
cat <<'EOF'
  getenforce
  sestatus
  setenforce 0                                   # pasar a permissive
  setenforce 1                                   # volver a enforcing
  ls -Z /var/www/html/
  ps auxZ | grep httpd
  getsebool -a | grep httpd
  setsebool -P httpd_can_network_connect_db on
  ausearch -m avc -ts recent                     # ver denegaciones en el log de auditoria
EOF

echo
echo "Demo de SELinux terminada."
