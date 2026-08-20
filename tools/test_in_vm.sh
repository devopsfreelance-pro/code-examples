#!/usr/bin/env bash
# VM QEMU desechable para probar ejemplos que modifican el sistema, simulando
# la maquina limpia de un lector. Crea overlay + cloud-init, bootea, copia el
# ejemplo adentro y deja un SSH listo. La VM se destruye con "destroy".
#
# Uso:
#   tools/test_in_vm.sh boot <nombre> [imagen-base]   # bootea y espera SSH
#   tools/test_in_vm.sh ssh  <nombre> -- <comando>    # ejecuta comando adentro
#   tools/test_in_vm.sh copy <nombre> <dir-local>     # copia un directorio a ~/
#   tools/test_in_vm.sh destroy <nombre>              # apaga y borra todo
#
# Imagen base por defecto: ~/.cache/qa-vms/noble-server-cloudimg-amd64.img
set -euo pipefail

CACHE=~/.cache/qa-vms
DEFAULT_IMG="$CACHE/noble-server-cloudimg-amd64.img"
ACTION="${1:?uso: boot|ssh|copy|destroy <nombre>}"
NAME="${2:?falta nombre de la VM}"
VMDIR="$CACHE/vm-$NAME"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -i $VMDIR/key"

port_of() { cat "$VMDIR/port"; }

case "$ACTION" in
  boot)
    BASE="${3:-$DEFAULT_IMG}"
    [ -f "$BASE" ] || { echo "imagen base inexistente: $BASE"; exit 1; }
    mkdir -p "$VMDIR"
    # puerto SSH libre determinista por nombre
    PORT=$(( 22000 + ($(echo -n "$NAME" | cksum | cut -d' ' -f1) % 1000) ))
    echo "$PORT" > "$VMDIR/port"
    ssh-keygen -q -t ed25519 -N '' -f "$VMDIR/key" <<< y >/dev/null 2>&1 || true
    qemu-img create -q -f qcow2 -b "$BASE" -F qcow2 "$VMDIR/disk.qcow2" 12G
    cat > "$VMDIR/user-data" <<EOF
#cloud-config
users:
  - name: lector
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - $(cat "$VMDIR/key.pub")
package_update: false
EOF
    echo "instance-id: qa-$NAME" > "$VMDIR/meta-data"
    genisoimage -quiet -output "$VMDIR/seed.iso" -volid cidata -joliet -rock "$VMDIR/user-data" "$VMDIR/meta-data" 2>/dev/null
    qemu-system-x86_64 \
      -enable-kvm -m 2048 -smp 2 -cpu host \
      -drive file="$VMDIR/disk.qcow2",if=virtio \
      -drive file="$VMDIR/seed.iso",if=virtio,format=raw \
      -netdev user,id=n0,hostfwd=tcp:127.0.0.1:$PORT-:22 -device virtio-net-pci,netdev=n0 \
      -display none -daemonize -pidfile "$VMDIR/pid"
    echo "esperando SSH en puerto $PORT..."
    for _ in $(seq 1 60); do
      if ssh $SSH_OPTS -p "$PORT" -o ConnectTimeout=3 lector@127.0.0.1 true 2>/dev/null; then
        echo "VM $NAME lista (puerto $PORT)"
        exit 0
      fi
      sleep 5
    done
    echo "timeout esperando SSH"; exit 1
    ;;
  ssh)
    shift 2; [ "${1:-}" = "--" ] && shift
    ssh $SSH_OPTS -p "$(port_of)" lector@127.0.0.1 "$@"
    ;;
  copy)
    DIRLOCAL="${3:?falta directorio}"
    scp $SSH_OPTS -P "$(port_of)" -q -r "$DIRLOCAL" lector@127.0.0.1:~/
    ;;
  destroy)
    [ -f "$VMDIR/pid" ] && kill "$(cat "$VMDIR/pid")" 2>/dev/null || true
    sleep 1
    rm -rf "$VMDIR"
    echo "VM $NAME destruida"
    ;;
  *)
    echo "accion desconocida: $ACTION"; exit 1 ;;
esac
