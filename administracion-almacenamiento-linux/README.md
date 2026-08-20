# Administración de almacenamiento en Linux: LVM sin downtime, demo ejecutable

Post: [Guía definitiva de administración de almacenamiento en Linux](https://www.devopsfreelance.pro/blog/posts/administracion-almacenamiento-linux/)

## Qué demuestra este ejemplo

El post explica que la ventaja real de LVM sobre particiones clásicas es
poder **crecer un volumen lógico y su filesystem en caliente**, con el
filesystem montado y datos existentes, usando `pvcreate` + `vgextend` +
`lvextend -r`.

Este ejemplo reproduce exactamente esa secuencia dentro de un contenedor
Docker privilegiado, usando dos archivos como "discos" (montados como loop
devices) para no necesitar hardware ni discos reales:

1. Crea un primer disco de 200MB, arma un volume group y un volumen lógico
   de 100MB con ext4, lo monta y escribe 60MB de datos.
2. Agrega un segundo disco de 150MB al volume group (`vgextend`).
3. Extiende el volumen lógico y el filesystem en un solo paso con
   `lvextend -r -L +100M`, sin desmontar ni detener nada.
4. Verifica que el filesystem pasó de 100MB a 200MB y que los datos
   escritos antes de la extensión siguen intactos.

Es el mismo flujo que describe la sección "LVM en la práctica: crecer sin
downtime" del post, incluyendo el uso del flag `-r` para evitar el error
clásico de extender el volumen y olvidarse de correr `resize2fs`.

## Requisitos

- Docker con Docker Compose v2 (`docker compose version`)
- Linux nativo con soporte de loop devices (`/dev/loop-control`). No
  funciona en Docker Desktop (macOS/Windows) porque la VM interna no
  expone loop devices reales al contenedor.
- El contenedor corre en modo `privileged` (necesario para `losetup`,
  `pvcreate`, `mount` dentro del contenedor). No requiere discos reales:
  todo se hace sobre archivos en `/demo/disks` dentro del propio
  contenedor.

## Cómo correrlo

```bash
cd administracion-almacenamiento-linux
docker compose build
docker compose run --rm lvm-demo
```

El contenedor se destruye al terminar (`--rm`); el script limpia
volume group y loop devices al salir aunque falle a mitad de camino.

## Salida esperada (resumida)

```
>>> 1. Creando 'disco' inicial de 200MB (archivo + loop device)
Disco 1: /dev/loop34

>>> 2. pvcreate + vgcreate + lvcreate (100MB) + filesystem ext4
  Physical volume "/dev/loop34" successfully created.
  Volume group "vgdemo" successfully created
  Logical volume "lvdatos" created.

>>> Estado inicial:
Filesystem                  Size  Used Avail Use% Mounted on
/dev/mapper/vgdemo-lvdatos   90M   24K   83M   1% /mnt/datos
  VG     #PV #LV #SN Attr   VSize   VFree
  vgdemo   1   1   0 wz--n- 196.00m 96.00m
  LV      VG     Attr       LSize
  lvdatos vgdemo -wi-ao---- 100.00m

>>> 3. Simulando datos en el volumen (60MB)
Filesystem                  Size  Used Avail Use% Mounted on
/dev/mapper/vgdemo-lvdatos   90M   61M   23M  73% /mnt/datos

>>> 4. Se necesita mas espacio: agregar un segundo 'disco' de 150MB
Disco 2: /dev/loop50
  Physical volume "/dev/loop50" successfully created.
  Volume group "vgdemo" successfully extended

>>> 5. lvextend -r: extiende el volumen logico Y el filesystem en un solo paso
  Size of logical volume vgdemo/lvdatos changed from 100.00 MiB (25 extents) to 200.00 MiB (50 extents).
  Logical volume vgdemo/lvdatos successfully resized.
resize2fs 1.47.0
The filesystem on /dev/mapper/vgdemo-lvdatos is now 51200 (4k) blocks long.

>>> Resultado tras el crecimiento en caliente (filesystem montado, sin downtime):
Filesystem                  Size  Used Avail Use% Mounted on
/dev/mapper/vgdemo-lvdatos  184M   61M  115M  35% /mnt/datos

>>> 6. Verificando que los datos previos siguen intactos
-rw-r--r-- 1 root root 60M Aug 20 14:26 /mnt/datos/archivo.dat

>>> Demo completa. El volumen crecio de 100MB a 200MB sin desmontar ni reiniciar nada.
```

Los tamaños exactos varían un poco por el overhead de LVM/ext4, pero el
punto central se ve siempre: el filesystem crece de ~90M a ~184M con el
volumen montado y sin perder el archivo de 60MB escrito antes. Salida
verificada corriendo el ejemplo tal cual está en este directorio.
