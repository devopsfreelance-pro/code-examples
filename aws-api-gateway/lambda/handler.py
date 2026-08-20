"""
Funcion Lambda minima que simula un endpoint de catalogo de productos.
Se invoca a traves de la integracion Lambda de API Gateway.
"""
import json


def handler(event, context):
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")

    body = {
        "message": "Hola desde AWS API Gateway + Lambda (LocalStack)",
        "method": method,
        "path": path,
        "productos": [
            {"id": 1, "nombre": "Laptop DevOps Edition", "precio": 1200},
            {"id": 2, "nombre": "Teclado mecanico", "precio": 80},
        ],
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
