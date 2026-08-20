"""
Simula la "plataforma cloud IoT" del post: solo recibe lo que el
edge ya filtro y agrego (alertas + resumenes), nunca el stream
crudo de sensores. Sirve para verificar visualmente que el edge
esta reduciendo el volumen de datos antes de salir.
"""
import os
import time

import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "mosquitto")
BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))


def connect_with_retry(client: mqtt.Client, host: str, port: int, retries: int = 10) -> None:
    for attempt in range(1, retries + 1):
        try:
            client.connect(host, port, keepalive=30)
            return
        except (ConnectionRefusedError, OSError) as exc:
            print(f"[cloud] broker no disponible aun (intento {attempt}/{retries}): {exc}")
            time.sleep(2)
    raise RuntimeError(f"No se pudo conectar a {host}:{port} tras {retries} intentos")


def on_connect(client: mqtt.Client, userdata, flags, rc) -> None:
    print(f"[cloud] conectado al broker (rc={rc}), suscribiendo a cloud/#")
    client.subscribe("cloud/#", qos=1)


def on_message(client: mqtt.Client, userdata, msg) -> None:
    print(f"[cloud] recibido en {msg.topic}: {msg.payload.decode()}")


def main() -> None:
    client = mqtt.Client(client_id="cloud-platform-mock")
    client.on_connect = on_connect
    client.on_message = on_message

    connect_with_retry(client, BROKER_HOST, BROKER_PORT)
    client.loop_forever()


if __name__ == "__main__":
    main()
