FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask==3.0.3

COPY incident_responder.py .

EXPOSE 5000

CMD ["python", "incident_responder.py"]
