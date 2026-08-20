"""
Simulador de sensores IoT (capa de percepcion).

Publica lecturas de temperatura de 3 sensores via MQTT, imitando el
ejemplo de ESP32 + MQTT del post. Cada pocos segundos, cada sensor
publica un JSON en el topico sensors/temperature/<device_id>.

De vez en cuando genera un pico de temperatura para que se vea el
filtrado de alertas en el edge processor.
"""
import json
import os
import random
import time

import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "mosquitto")
BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
PUBLISH_INTERVAL_SECONDS = float(os.environ.get("PUBLISH_INTERVAL_SECONDS", "3"))

DEVICES = ["temp-001", "temp-002", "temp-003"]


def connect_with_retry(client: mqtt.Client, host: str, port: int, retries: int = 10) -> None:
    for attempt in range(1, retries + 1):
        try:
            client.connect(host, port, keepalive=30)
            return
        except (ConnectionRefusedError, OSError) as exc:
            print(f"[simulator] broker no disponible aun (intento {attempt}/{retries}): {exc}")
            time.sleep(2)
    raise RuntimeError(f"No se pudo conectar a {host}:{port} tras {retries} intentos")


def read_temperature(device_id: str) -> float:
    """Genera una lectura realista, con picos ocasionales (~1 de cada 6)."""
    base = 22.0 + random.uniform(-2.0, 2.0)
    if random.random() < 0.17:
        base += random.uniform(10.0, 18.0)  # simula anomalia termica
    return round(base, 2)


def main() -> None:
    client = mqtt.Client(client_id="sensor-simulator")
    connect_with_retry(client, BROKER_HOST, BROKER_PORT)
    client.loop_start()

    print(f"[simulator] publicando lecturas cada {PUBLISH_INTERVAL_SECONDS}s a {BROKER_HOST}:{BROKER_PORT}")

    try:
        while True:
            for device_id in DEVICES:
                temperature = read_temperature(device_id)
                topic = f"sensors/temperature/{device_id}"
                payload = json.dumps(
                    {
                        "device_id": device_id,
                        "temperature": temperature,
                        "timestamp": time.time(),
                    }
                )
                client.publish(topic, payload, qos=1)
                print(f"[simulator] {topic} -> {temperature}C")
            time.sleep(PUBLISH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
