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

# Clave pública del lector (generada en el paso 1 del README)
COPY authorized_keys /home/deploy/.ssh/authorized_keys
RUN chmod 600 /home/deploy/.ssh/authorized_keys && \
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
