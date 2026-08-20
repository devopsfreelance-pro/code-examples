FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt==1.6.1

COPY sensor_simulator.py edge_processor.py cloud_monitor.py ./

CMD ["python", "sensor_simulator.py"]
