#!/bin/bash
# Demuestra el flujo central del post: gestión de paquetes RPM + repositorio
# interno propio, tal como se haría en un entorno RHEL/CentOS empresarial.
set -euo pipefail

echo "=== 1) Verificar la integridad de paquetes instalados ==="
rpm -Va --pkgverify | head -n 10 || true

echo
echo "=== 2) Consultar información detallada de un paquete (httpd) ==="
rpm -qi httpd

echo
echo "=== 3) Listar archivos instalados por un paquete (nginx) ==="
rpm -ql nginx | head -n 10

echo
echo "=== 4) Identificar qué paquete provee un archivo del sistema ==="
rpm -qf /usr/bin/python3

echo
echo "=== 5) Crear un repositorio interno con los RPM ya cacheados por dnf ==="
REPO_DIR=/demo/repo/rocky/9/internal
mkdir -p "$REPO_DIR"

# Copiamos al repo interno los .rpm que dnf ya descargó al instalar httpd/nginx,
# simulando el escenario del post: "repositorios internos con versiones
# específicas de software, controladas por la organización".
find /var/cache/dnf -name '*.rpm' -exec cp {} "$REPO_DIR" \; 2>/dev/null || true

if [ -z "$(ls -A "$REPO_DIR" 2>/dev/null)" ]; then
  echo "No se encontraron .rpm cacheados; se descarga uno de referencia (tree) para poblar el repo."
  dnf install -y --downloadonly --downloaddir="$REPO_DIR" tree
fi

createrepo_c "$REPO_DIR"

echo
echo "=== 6) Configurar el repositorio interno (equivalente a /etc/yum.repos.d/internal.repo) ==="
cat > /etc/yum.repos.d/internal.repo <<EOF
[internal-base]
name=Internal Base Repository
baseurl=file://${REPO_DIR}
enabled=1
gpgcheck=0
EOF

echo
echo "=== 7) Consultar el repositorio interno recién creado ==="
dnf repolist internal-base
dnf --repo=internal-base list available 2>/dev/null | head -n 15

echo
echo "=== Demo completa: paquetes instalados, metadatos consultados y repo interno operativo. ==="
