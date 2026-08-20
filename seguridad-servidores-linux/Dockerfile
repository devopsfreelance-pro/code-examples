FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        ufw \
        fail2ban \
        sudo \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Servidor a proposito con configuracion insegura, tal como llegaria
# recien provisionado (root login habilitado, password auth activo,
# sin firewall, sin fail2ban corriendo). El script audit.sh detecta
# estos problemas y hardening.sh los corrige.
RUN mkdir -p /var/run/sshd && \
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    echo 'root:root' | chpasswd

COPY audit.sh /usr/local/bin/audit.sh
COPY hardening.sh /usr/local/bin/hardening.sh
RUN chmod +x /usr/local/bin/audit.sh /usr/local/bin/hardening.sh

CMD ["/usr/sbin/sshd", "-D"]
