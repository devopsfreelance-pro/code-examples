#!/bin/bash
# audit-hardening.sh
#
# Verifica, dentro del servidor Ubuntu, que las medidas de hardening
# descritas en el post "Ubuntu Server para producción" estén aplicadas:
#   - SSH endurecido (sin passwords, sin root, puerto no estándar, etc.)
# - actualizaciones desatendidas limitadas a parches de seguridad
#   - reglas de auditoría de archivos sensibles
#
# Se ejecuta DENTRO del contenedor de demo:
#   docker compose exec ubuntu-hardened bash /scripts/audit-hardening.sh
#
# Salida: un check por línea (OK/FAIL) y un score final sobre 100.

set -uo pipefail

SSHD_CONFIG="/etc/ssh/sshd_config"
UNATTENDED_CONFIG="/etc/apt/apt.conf.d/50unattended-upgrades"
AUDIT_RULES="/etc/audit/rules.d/audit.rules"

total=0
passed=0

check() {
    local description="$1"
    local condition="$2"
    total=$((total + 1))
    if eval "$condition"; then
        echo "[OK]   $description"
        passed=$((passed + 1))
    else
        echo "[FAIL] $description"
    fi
}

echo "== Hardening de SSH ($SSHD_CONFIG) =="
check "Puerto SSH distinto de 22" "grep -qE '^Port 2222' '$SSHD_CONFIG'"
check "Login root deshabilitado" "grep -qE '^PermitRootLogin no' '$SSHD_CONFIG'"
check "Autenticación por password deshabilitada" "grep -qE '^PasswordAuthentication no' '$SSHD_CONFIG'"
check "Autenticación por clave pública habilitada" "grep -qE '^PubkeyAuthentication yes' '$SSHD_CONFIG'"
check "Lista blanca de usuarios (AllowUsers) presente" "grep -qE '^AllowUsers' '$SSHD_CONFIG'"
check "MaxAuthTries restringido (<=3)" "grep -qE '^MaxAuthTries [1-3]$' '$SSHD_CONFIG'"

echo
echo "== Actualizaciones desatendidas ($UNATTENDED_CONFIG) =="
check "Solo se permiten actualizaciones de seguridad" "grep -q 'distro_codename}-security' '$UNATTENDED_CONFIG'"
check "Reinicio automático deshabilitado" "grep -qE 'Automatic-Reboot \"false\"' '$UNATTENDED_CONFIG'"

echo
echo "== Auditoría de archivos sensibles ($AUDIT_RULES) =="
check "Vigila /etc/passwd" "grep -q '/etc/passwd' '$AUDIT_RULES'"
check "Vigila /etc/shadow" "grep -q '/etc/shadow' '$AUDIT_RULES'"
check "Vigila /etc/sudoers" "grep -q '/etc/sudoers' '$AUDIT_RULES'"

echo
score=$(( passed * 100 / total ))
echo "Resultado: $passed/$total checks OK (score: ${score}/100)"

if [ "$passed" -ne "$total" ]; then
    exit 1
fi
