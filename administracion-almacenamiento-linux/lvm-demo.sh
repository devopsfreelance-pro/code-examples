#!/bin/bash
# Demo de LVM: crecer un volumen logico y su filesystem sin downtime,
# usando archivos como "discos" (loop devices) para no requerir hardware real.
set -euo pipefail

DISK_DIR="/demo/disks"
MOUNT_POINT="/mnt/datos"
VG_NAME="vgdemo"
LV_NAME="lvdatos"

log() { echo -e "\n>>> $*"; }

cleanup() {
    log "Limpiando (umount, vg, loop devices)..."
    umount "$MOUNT_POINT" 2>/dev/null || true
    lvchange -an "/dev/${VG_NAME}/${LV_NAME}" 2>/dev/null || true
    vgremove -f "$VG_NAME" 2>/dev/null || true
    for img in "$DISK_DIR/disk1.img" "$DISK_DIR/disk2.img"; do
        for dev in $(losetup -j "$img" 2>/dev/null | cut -d: -f1); do
            losetup -d "$dev" 2>/dev/null || true
        done
    done
}
trap cleanup EXIT

mkdir -p "$DISK_DIR" "$MOUNT_POINT"

log "1. Creando 'disco' inicial de 200MB (archivo + loop device)"
rm -f "$DISK_DIR/disk1.img"
truncate -s 200M "$DISK_DIR/disk1.img"
DISK1=$(losetup --find --show "$DISK_DIR/disk1.img")
echo "Disco 1: $DISK1"

log "2. pvcreate + vgcreate + lvcreate (100MB) + filesystem ext4"
pvcreate -f "$DISK1"
vgcreate "$VG_NAME" "$DISK1"
# -Zn -Wn: sin udev en el contenedor, el paso de "zero new LV" de lvcreate
# no encuentra el nodo /dev/mapper a tiempo y aborta; lo saltamos (es un
# volumen de demo sobre un loop device vacio, no un caso con datos previos).
lvcreate -Zn -Wn -L 100M -n "$LV_NAME" "$VG_NAME"
mkfs.ext4 -q "/dev/${VG_NAME}/${LV_NAME}"
mount "/dev/${VG_NAME}/${LV_NAME}" "$MOUNT_POINT"

log "Estado inicial:"
df -h "$MOUNT_POINT"
vgs "$VG_NAME"
lvs "$VG_NAME"

log "3. Simulando datos en el volumen (60MB)"
dd if=/dev/zero of="$MOUNT_POINT/archivo.dat" bs=1M count=60 status=none
df -h "$MOUNT_POINT"

log "4. Se necesita mas espacio: agregar un segundo 'disco' de 150MB"
rm -f "$DISK_DIR/disk2.img"
truncate -s 150M "$DISK_DIR/disk2.img"
DISK2=$(losetup --find --show "$DISK_DIR/disk2.img")
echo "Disco 2: $DISK2"

pvcreate -f "$DISK2"
vgextend "$VG_NAME" "$DISK2"

log "5. lvextend -r: extiende el volumen logico Y el filesystem en un solo paso"
lvextend -r -L +100M "/dev/${VG_NAME}/${LV_NAME}"

log "Resultado tras el crecimiento en caliente (filesystem montado, sin downtime):"
df -h "$MOUNT_POINT"
vgs "$VG_NAME"
lvs "$VG_NAME"

log "6. Verificando que los datos previos siguen intactos"
ls -lh "$MOUNT_POINT/archivo.dat"

log "Demo completa. El volumen crecio de 100MB a 200MB sin desmontar ni reiniciar nada."
