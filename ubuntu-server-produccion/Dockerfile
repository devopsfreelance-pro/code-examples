# Demo de hardening de Ubuntu Server para producción
# Basado en: https://www.devopsfreelance.pro/blog/posts/ubuntu-server-produccion/
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        sudo \
        unattended-upgrades \
        auditd \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd /etc/audit/rules.d

# Usuario de despliegue (equivalente al "deploy" del sshd_config endurecido)
RUN useradd -m -s /bin/bash deploy && \
    usermod -aG sudo deploy && \
    mkdir -p /home/deploy/.ssh && \
    chmod 700 /home/deploy/.ssh

# Par de claves de demo generado dentro de la imagen: así "docker compose up"
# funciona sin material externo. La privada se extrae luego con
# "docker compose cp" (ver README) para probar la conexión SSH.
RUN ssh-keygen -t ed25519 -f /home/deploy/.ssh/id_demo -N "" -q -C "demo@ubuntu-hardened" && \
    cp /home/deploy/.ssh/id_demo.pub /home/deploy/.ssh/authorized_keys && \
    chmod 600 /home/deploy/.ssh/authorized_keys /home/deploy/.ssh/id_demo && \
    chown -R deploy:deploy /home/deploy/.ssh

# Configuraciones endurecidas tomadas directamente del post
COPY config/sshd_config /etc/ssh/sshd_config
COPY config/50unattended-upgrades /etc/apt/apt.conf.d/50unattended-upgrades
COPY config/audit.rules /etc/audit/rules.d/audit.rules

COPY scripts/audit-hardening.sh /scripts/audit-hardening.sh
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /scripts/audit-hardening.sh /entrypoint.sh

EXPOSE 2222

ENTRYPOINT ["/entrypoint.sh"]
