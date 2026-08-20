"""
Gateway de edge computing (capa de edge del post).

Se suscribe a sensors/temperature/# y aplica la logica de filtrado
que describe el post: solo lo que supera el umbral se reenvia como
alerta "a la nube" (topico cloud/alerts/temperature); el resto se
guarda localmente y se agrega en un resumen periodico, reduciendo el
volumen de datos que sale del edge.
"""
import json
import os
import time
from collections import defaultdict

import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "mosquitto")
BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
TEMPERATURE_THRESHOLD = float(os.environ.get("TEMPERATURE_THRESHOLD", "30"))
SUMMARY_INTERVAL_SECONDS = float(os.environ.get("SUMMARY_INTERVAL_SECONDS", "20"))

local_readings = defaultdict(list)


def connect_with_retry(client: mqtt.Client, host: str, port: int, retries: int = 10) -> None:
    for attempt in range(1, retries + 1):
        try:
            client.connect(host, port, keepalive=30)
            return
        except (ConnectionRefusedError, OSError) as exc:
            print(f"[edge] broker no disponible aun (intento {attempt}/{retries}): {exc}")
            time.sleep(2)
    raise RuntimeError(f"No se pudo conectar a {host}:{port} tras {retries} intentos")


def on_connect(client: mqtt.Client, userdata, flags, rc) -> None:
    print(f"[edge] conectado al broker (rc={rc}), suscribiendo a sensors/temperature/#")
    client.subscribe("sensors/temperature/#", qos=1)


def on_message(client: mqtt.Client, userdata, msg) -> None:
    try:
        data = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print(f"[edge] payload invalido en {msg.topic}, se descarta")
        return

    device_id = data.get("device_id", "unknown")
    temperature = data.get("temperature")

    if temperature is None:
        return

    if temperature > TEMPERATURE_THRESHOLD:
        alert = {
            "device_id": device_id,
            "temperature": temperature,
            "threshold": TEMPERATURE_THRESHOLD,
            "processed_by": "edge-gateway-local",
            "timestamp": time.time(),
        }
        client.publish("cloud/alerts/temperature", json.dumps(alert), qos=1)
        print(f"[edge] ALERTA enviada a la nube: {device_id} = {temperature}C (> {TEMPERATURE_THRESHOLD}C)")
    else:
        local_readings[device_id].append(temperature)
        print(f"[edge] dato normal almacenado localmente: {device_id} = {temperature}C")


def publish_periodic_summary(client: mqtt.Client) -> None:
    if not local_readings:
        return

    summary = {}
    for device_id, readings in local_readings.items():
        summary[device_id] = {
            "count": len(readings),
            "avg_temperature": round(sum(readings) / len(readings), 2),
            "min_temperature": min(readings),
            "max_temperature": max(readings),
        }

    payload = json.dumps({"timestamp": time.time(), "devices": summary})
    client.publish("cloud/summaries/periodic", payload, qos=1)
    print(f"[edge] resumen periodico enviado a la nube: {payload}")
    local_readings.clear()


def main() -> None:
    client = mqtt.Client(client_id="edge-gateway-local")
    client.on_connect = on_connect
    client.on_message = on_message

    connect_with_retry(client, BROKER_HOST, BROKER_PORT)
    client.loop_start()

    print(f"[edge] umbral de alerta: {TEMPERATURE_THRESHOLD}C, resumen cada {SUMMARY_INTERVAL_SECONDS}s")

    try:
        while True:
            time.sleep(SUMMARY_INTERVAL_SECONDS)
            publish_periodic_summary(client)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
