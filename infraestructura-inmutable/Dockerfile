# Dockerfile = equivalente local a un template de Packer.
# Igual que golden-image.pkr.hcl del post: parte de una base, instala
# dependencias, copia la app y hornea la version en la imagen. El
# resultado es una "golden image" inmutable: para cambiar algo se
# reconstruye y se re-despliega, nunca se edita un contenedor corriendo.

FROM python:3.12-alpine

# La version se hornea en build time, no se inyecta despues del deploy.
ARG APP_VERSION=v1
ARG DEPLOYMENT_COLOR=blue
ENV APP_VERSION=${APP_VERSION}
ENV DEPLOYMENT_COLOR=${DEPLOYMENT_COLOR}
ENV PORT=8080

WORKDIR /opt/webapp
COPY app/server.py .

# "Hardening" minimo: usuario sin privilegios, igual que os-hardening.sh
# en el post
RUN adduser -D -H appuser
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=3s --start-period=3s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1

CMD ["python3", "server.py"]
