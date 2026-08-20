FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    flask==3.0.3 \
    requests==2.32.3 \
    opentelemetry-api==1.25.0 \
    opentelemetry-sdk==1.25.0 \
    opentelemetry-exporter-otlp-proto-grpc==1.25.0 \
    opentelemetry-instrumentation-flask==0.46b0 \
    opentelemetry-instrumentation-requests==0.46b0

COPY app.py .

EXPOSE 5001

CMD ["python", "app.py"]
