FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask==3.0.3 psycopg2-binary==2.9.9

COPY payment_service.py .

EXPOSE 8080

CMD ["python", "payment_service.py"]
