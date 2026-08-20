FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        lvm2 \
        e2fsprogs \
        xfsprogs \
        util-linux \
        parted \
    && rm -rf /var/lib/apt/lists/*

# En contenedores no corre udev, asi que LVM debe manejar los nodos de
# dispositivo el mismo (sin esto, "pvcreate/lvcreate" fallan con
# "device not cleared" porque esperan que udev cree /dev/mapper/*).
RUN sed -i \
        -e 's/udev_sync = 1/udev_sync = 0/' \
        -e 's/udev_rules = 1/udev_rules = 0/' \
        -e 's/obtain_device_list_from_udev = 1/obtain_device_list_from_udev = 0/' \
        /etc/lvm/lvm.conf

WORKDIR /demo
COPY lvm-demo.sh /demo/lvm-demo.sh
RUN chmod +x /demo/lvm-demo.sh

ENTRYPOINT ["/demo/lvm-demo.sh"]
