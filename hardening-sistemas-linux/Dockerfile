FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        lynis \
        auditd \
        audispd-plugins \
        sudo \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY sysctl-hardening.conf /opt/hardening/sysctl-hardening.conf
COPY audit-hardening.rules /opt/hardening/audit-hardening.rules
COPY harden.sh /usr/local/bin/harden.sh

RUN chmod +x /usr/local/bin/harden.sh

WORKDIR /opt/hardening

CMD ["sleep", "infinity"]
