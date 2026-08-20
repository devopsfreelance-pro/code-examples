"""
Simula el modelo de ejecución "serverless": cada invocación arranca un
proceso (intérprete) nuevo desde cero, procesa un único evento y termina.
No hay proceso persistente ni estado compartido entre invocaciones, tal
como ocurre con una función Lambda cuando no hay una instancia "caliente"
disponible (cold start).
"""
import json
import sys


def process(text: str) -> dict:
    """Misma lógica de negocio que app.py, para comparar en igualdad de condiciones."""
    return {
        "words": len(text.split()),
        "chars": len(text),
        "reversed": text[::-1],
    }


def lambda_handler(event: dict) -> dict:
    text = event.get("text", "hola mundo")
    return {"statusCode": 200, "body": process(text)}


if __name__ == "__main__":
    # El "evento" llega como argumento de línea de comandos, simulando
    # el payload que dispararía la función (API Gateway, S3, etc).
    input_text = sys.argv[1] if len(sys.argv) > 1 else "hola mundo"
    event = {"text": input_text}
    response = lambda_handler(event)
    print(json.dumps(response))
