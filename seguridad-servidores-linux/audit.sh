#!/usr/bin/env bash
# audit.sh - Mini auditoria de hardening estilo CIS Benchmark para Linux.
#
# Revisa un subconjunto de los controles mencionados en el post
# "Seguridad en servidores Linux: Guia esencial para DevOps":
#   - SSH: root login y autenticacion por password
#   - Firewall (ufw) activo
#   - fail2ban corriendo (proteccion fuerza bruta)
#   - Politica de contraseñas (PASS_MAX_DAYS)
#   - Archivos con permisos de escritura para "otros" en /etc
#
# Salida: por cada control imprime [OK] o [FAIL] y al final un resumen
# con codigo de salida != 0 si hay fallas (util para CI/CD).

set -u

PASS=0
FAIL=0

check() {
    local description="$1"
    local status="$2" # 0 = ok, 1 = fail
    if [ "$status" -eq 0 ]; then
        echo "[OK]   $description"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $description"
        FAIL=$((FAIL + 1))
    fi
}

echo "== Auditoria de hardening Linux =="
echo

# 1. SSH: PermitRootLogin debe estar deshabilitado
if grep -qE '^\s*PermitRootLogin\s+(no|prohibit-password)\s*$' /etc/ssh/sshd_config 2>/dev/null; then
    check "SSH: PermitRootLogin deshabilitado" 0
else
    check "SSH: PermitRootLogin deshabilitado" 1
fi

# 2. SSH: PasswordAuthentication debe estar deshabilitado (solo claves)
if grep -qE '^\s*PasswordAuthentication\s+no\s*$' /etc/ssh/sshd_config 2>/dev/null; then
    check "SSH: PasswordAuthentication deshabilitado (solo claves)" 0
else
    check "SSH: PasswordAuthentication deshabilitado (solo claves)" 1
fi

# 3. Firewall (ufw) activo
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -qi "Status: active"; then
    check "Firewall (ufw) activo" 0
else
    check "Firewall (ufw) activo" 1
fi

# 4. fail2ban corriendo
if pgrep -x fail2ban-server >/dev/null 2>&1; then
    check "fail2ban activo (proteccion contra fuerza bruta)" 0
else
    check "fail2ban activo (proteccion contra fuerza bruta)" 1
fi

# 5. Politica de expiracion de contraseñas (<= 90 dias)
max_days=$(grep -E '^PASS_MAX_DAYS' /etc/login.defs 2>/dev/null | awk '{print $2}')
if [ -n "${max_days:-}" ] && [ "$max_days" -le 90 ]; then
    check "Politica de contraseñas: PASS_MAX_DAYS <= 90 (actual: $max_days)" 0
else
    check "Politica de contraseñas: PASS_MAX_DAYS <= 90 (actual: ${max_days:-no configurado})" 1
fi

# 6. Sin archivos world-writable en /etc
world_writable=$(find /etc -xdev -type f -perm -0002 2>/dev/null | wc -l)
if [ "$world_writable" -eq 0 ]; then
    check "Sin archivos world-writable en /etc" 0
else
    check "Sin archivos world-writable en /etc (encontrados: $world_writable)" 1
fi

echo
echo "== Resumen: $PASS OK / $FAIL FAIL =="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
