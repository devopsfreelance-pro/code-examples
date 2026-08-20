# Imagen Ubuntu con systemd como PID 1, para poder ejecutar systemctl/journalctl
# de forma real dentro de un contenedor (patron estandar para demos de systemd
# en Docker: systemd corre como init, no como proceso comun).
FROM ubuntu:22.04

ENV container=docker
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends systemd systemd-sysv python3 curl ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && systemctl set-default multi-user.target \
    # Desactivar unidades que no aportan a la demo y ralentizan/rompen el arranque en contenedor
    && systemctl mask systemd-udevd.service systemd-udevd-kernel.socket \
       systemd-udev-trigger.service getty.target getty-static.service

COPY app/server.py /opt/webapp/server.py
COPY webapp.service /etc/systemd/system/webapp.service

RUN chmod +x /opt/webapp/server.py \
    && systemctl enable webapp.service

STOPSIGNAL SIGRTMIN+3

VOLUME ["/sys/fs/cgroup"]

CMD ["/sbin/init"]
