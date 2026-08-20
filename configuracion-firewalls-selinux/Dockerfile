FROM rockylinux:9

RUN dnf install -y \
        iptables \
        firewalld \
        policycoreutils \
        policycoreutils-python-utils \
        setools-console \
        procps-ng \
        iproute \
        httpd \
    && dnf clean all

WORKDIR /lab
COPY scripts/ /lab/scripts/
RUN chmod +x /lab/scripts/*.sh

CMD ["sleep", "infinity"]
