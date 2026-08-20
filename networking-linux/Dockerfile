FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        iproute2 \
        iptables \
        nftables \
        iputils-ping \
    ; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY netns-demo.sh iptables-vs-nftables.sh cleanup.sh /lab/
RUN chmod +x /lab/*.sh

CMD ["sleep", "infinity"]
