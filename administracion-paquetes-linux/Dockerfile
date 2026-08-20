FROM ubuntu:24.04

# Evita prompts interactivos durante la instalación (igual que en pipelines de CI/CD)
ENV DEBIAN_FRONTEND=noninteractive

# Copiamos el pin de versión y el script de instalación
COPY preferences.d/nginx-pin /etc/apt/preferences.d/nginx-pin
COPY install.sh /usr/local/bin/install.sh
RUN chmod +x /usr/local/bin/install.sh

CMD ["/usr/local/bin/install.sh"]
