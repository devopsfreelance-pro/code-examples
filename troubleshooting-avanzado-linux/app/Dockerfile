FROM python:3.11-slim

WORKDIR /app
COPY leaky_app.py .

# procps: para tener ps/top/free disponibles dentro del contenedor
# durante el diagnostico (docker exec).
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

CMD ["python3", "-u", "leaky_app.py"]
