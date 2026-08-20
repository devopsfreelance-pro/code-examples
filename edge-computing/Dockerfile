FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir prometheus_client==0.20.0

COPY sensor_exporter.py .

EXPOSE 9100

CMD ["python", "sensor_exporter.py"]
