#!/bin/bash
# Aplica un subconjunto de controles de hardening inspirados en CIS Benchmarks
# sobre el sistema donde corre (pensado para el contenedor de este laboratorio,
# pero los mismos pasos aplican a un servidor Ubuntu/Debian real con sudo).
set -euo pipefail

echo "== Aplicando hardening de kernel (sysctl) =="
cp /opt/hardening/sysctl-hardening.conf /etc/sysctl.d/99-hardening.conf
if sysctl -p /etc/sysctl.d/99-hardening.conf 2>/dev/null; then
  echo "  parametros de kernel aplicados"
else
  echo "  algunos parametros no se pudieron aplicar en el contenedor (namespace de red/kernel"
  echo "  restringido por Docker); en un host real se aplican con 'sysctl --system' o al reiniciar"
fi

echo "== Configurando reglas de auditd (registro de eventos criticos) =="
mkdir -p /etc/audit/rules.d
cp /opt/hardening/audit-hardening.rules /etc/audit/rules.d/hardening.rules
chmod 640 /etc/audit/rules.d/hardening.rules
echo "  reglas escritas en /etc/audit/rules.d/hardening.rules"

echo "== Restringiendo permisos de archivos sensibles =="
chmod 600 /etc/shadow
chmod 644 /etc/passwd
chmod 640 /etc/group

echo "== Deshabilitando core dumps de binarios setuid =="
if ! grep -q '^\* hard core 0$' /etc/security/limits.conf 2>/dev/null; then
  echo '* hard core 0' >> /etc/security/limits.conf
fi

echo "== Politica de contrasenas y umask en /etc/login.defs =="
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/'  /etc/login.defs
sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   7/'   /etc/login.defs
sed -i 's/^UMASK.*/UMASK           027/'         /etc/login.defs
if ! grep -q '^ENCRYPT_METHOD SHA512$' /etc/login.defs 2>/dev/null; then
  echo 'ENCRYPT_METHOD SHA512' >> /etc/login.defs
fi

echo "== Banner legal en /etc/issue y /etc/issue.net =="
cat > /etc/issue <<'EOF'
Acceso restringido. Esta actividad puede ser monitoreada y auditada.
El uso no autorizado esta prohibido y sera perseguido.
EOF
cp /etc/issue /etc/issue.net

echo "== Hardening aplicado =="
