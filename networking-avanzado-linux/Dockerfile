FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        iproute2 \
        iputils-ping \
        netcat-openbsd \
        coreutils \
        bc \
    ; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY policy-routing-lab.sh tc-bandwidth-shaping.sh cleanup.sh /lab/
RUN chmod +x /lab/*.sh

CMD ["sleep", "infinity"]
