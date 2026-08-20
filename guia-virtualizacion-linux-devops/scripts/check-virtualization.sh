#!/usr/bin/env bash
# check-virtualization.sh
# Diagnostica el soporte de virtualizacion de hardware (KVM) en un host Linux
# y compara los niveles de aislamiento disponibles: KVM, LXC/LXD, Docker/Podman.
#
# Uso:
#   ./check-virtualization.sh
#
# No requiere permisos de root para el diagnostico basico. Algunos checks
# opcionales (kvm-ok) piden sudo si la herramienta esta instalada.

set -euo pipefail

green() { printf '\033[32m%s\033[0m\n' "$1"; }
red()   { printf '\033[31m%s\033[0m\n' "$1"; }
yellow() { printf '\033[33m%s\033[0m\n' "$1"; }

echo "== Diagnostico de virtualizacion Linux =="
echo

# 1. Extensiones de virtualizacion del CPU (Intel VT-x / AMD-V)
echo "-- 1. Extensiones de CPU (vmx/svm) --"
VMX_COUNT=$(egrep -c '(vmx|svm)' /proc/cpuinfo || true)
if [ "$VMX_COUNT" -gt 0 ]; then
  green "OK: el CPU expone $VMX_COUNT extensiones de virtualizacion (vmx/svm)"
else
  red "FALTA: el CPU no expone vmx/svm. KVM no funcionara en este host."
fi
echo

# 2. Modulo de kernel KVM cargado
echo "-- 2. Modulo KVM en el kernel --"
if lsmod | grep -q '^kvm'; then
  green "OK: modulo kvm cargado"
  lsmod | grep '^kvm' | awk '{print "  - "$1}'
else
  yellow "AVISO: modulo kvm no cargado (puede que el host no lo necesite, ej. VM anidada)"
fi
echo

# 3. kvm-ok si esta disponible (Debian/Ubuntu)
echo "-- 3. kvm-ok (si esta instalado) --"
if command -v kvm-ok >/dev/null 2>&1; then
  sudo kvm-ok || true
else
  yellow "kvm-ok no instalado. Instalar con: sudo apt install cpu-checker"
fi
echo

# 4. Herramientas de gestion de contenedores/VMs disponibles
echo "-- 4. Herramientas instaladas --"
for tool in virsh virt-install lxc docker podman; do
  if command -v "$tool" >/dev/null 2>&1; then
    green "OK: $tool disponible ($(command -v "$tool"))"
  else
    yellow "no instalado: $tool"
  fi
done
echo

# 5. Resumen de niveles de aislamiento (informativo)
echo "-- 5. Resumen de aislamiento --"
cat <<'EOF'
  KVM            : kernel propio por VM, aislamiento fuerte, overhead alto
  LXC/LXD        : kernel compartido, namespace de sistema completo, overhead bajo
  Docker/Podman  : kernel compartido, aislamiento de proceso, overhead minimo
EOF

echo
echo "Diagnostico completo."
