#!/usr/bin/env bash
# hardening.sh - Aplica correcciones automaticas para los controles que
# audit.sh detecta como [FAIL]. Pensado para correr una sola vez sobre
# un servidor recien provisionado.
#
# Uso: sudo ./hardening.sh

set -eu

echo "== Aplicando hardening =="

# 1. SSH: deshabilitar login de root
if [ -f /etc/ssh/sshd_config ]; then
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    echo "[hardening] PermitRootLogin -> no"
fi

# 2. SSH: forzar autenticacion por clave (deshabilitar password)
if [ -f /etc/ssh/sshd_config ]; then
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    echo "[hardening] PasswordAuthentication -> no"
fi

# 3. Firewall: politica por defecto deny + permitir solo SSH
if command -v ufw >/dev/null 2>&1; then
    ufw --force default deny incoming || echo "[hardening] aviso: ufw requiere --cap-add NET_ADMIN,NET_RAW en el contenedor"
    ufw --force default allow outgoing || true
    ufw allow ssh || true
    ufw --force enable || true
    echo "[hardening] ufw configurado (deny incoming, allow ssh)"
fi

# 4. fail2ban: arrancar el servicio
if command -v fail2ban-server >/dev/null 2>&1; then
    fail2ban-client start >/dev/null 2>&1 || service fail2ban start || true
    echo "[hardening] fail2ban iniciado"
fi

# 5. Politica de contraseñas: expiracion maxima 90 dias
if [ -f /etc/login.defs ]; then
    sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/' /etc/login.defs
    if ! grep -q '^PASS_MAX_DAYS' /etc/login.defs; then
        echo "PASS_MAX_DAYS   90" >>/etc/login.defs
    fi
    echo "[hardening] PASS_MAX_DAYS -> 90"
fi

# 6. Permisos: quitar bit world-writable de archivos en /etc
find /etc -xdev -type f -perm -0002 -exec chmod o-w {} \; 2>/dev/null || true
echo "[hardening] permisos world-writable removidos en /etc"

# 7. Recargar sshd para que los cambios de PermitRootLogin/PasswordAuthentication
# tomen efecto. OJO: en un contenedor donde sshd corre como PID 1 en foreground
# (sin systemd), "service ssh restart" MATA el proceso principal y tira abajo
# el contenedor entero. Por eso se recarga con SIGHUP (sshd relee su config sin
# perder el PID) en vez de reiniciar el proceso. En un servidor real con systemd
# se usa el reload nativo, que es igual de seguro.
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    systemctl reload ssh 2>/dev/null || systemctl reload sshd 2>/dev/null || true
    echo "[hardening] sshd recargado (systemctl reload)"
else
    sshd_pid="$(cat /run/sshd.pid 2>/dev/null || true)"
    [ -n "$sshd_pid" ] || sshd_pid="$(pgrep -x sshd 2>/dev/null | head -1 || true)"
    if [ -n "$sshd_pid" ] && kill -HUP "$sshd_pid" 2>/dev/null; then
        echo "[hardening] sshd recargado (SIGHUP a PID $sshd_pid, sin matar el proceso)"
    else
        echo "[hardening] aviso: no se pudo recargar sshd automaticamente; los cambios de SSH quedan en el archivo pero no aplican hasta el proximo reinicio del servicio"
    fi
fi

echo
echo "Hardening aplicado."
