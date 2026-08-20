FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY node_metrics_exporter.py .

EXPOSE 8000

CMD ["python", "node_metrics_exporter.py"]
