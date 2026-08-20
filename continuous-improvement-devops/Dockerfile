FROM python:3.12-slim

WORKDIR /demo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# __init__.py vacios para que "from sample_app.calculator import calculate"
# funcione como paquete dentro del contenedor.
RUN touch sample_app/__init__.py tests/__init__.py

CMD ["bash", "run_demo.sh"]
