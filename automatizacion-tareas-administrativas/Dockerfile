FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/scripts

COPY scripts/cleanup-logs.sh /opt/scripts/cleanup-logs.sh
COPY scripts/entrypoint.sh /opt/scripts/entrypoint.sh
COPY crontab /etc/cron.d/admin-automation

RUN chmod +x /opt/scripts/cleanup-logs.sh /opt/scripts/entrypoint.sh \
    && chmod 0644 /etc/cron.d/admin-automation \
    && mkdir -p /var/log/app /var/lock

ENTRYPOINT ["/opt/scripts/entrypoint.sh"]
