# Imagen base deliberadamente vieja para que Trivy encuentre CVEs conocidos
# del sistema operativo base. NO usar esta version en un proyecto real.
FROM python:3.9-slim-bullseye

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py .

EXPOSE 5000

CMD ["python", "app.py"]
