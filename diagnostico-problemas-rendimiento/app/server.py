"""
Demo app minima para el ejemplo de diagnostico de problemas de rendimiento.

Expone dos endpoints que hacen exactamente el mismo trabajo "costoso"
(una consulta simulada de ~300ms), uno sin cache y otro con el patron
de caching en Redis que describe el post:

  GET /slow         -> siempre ejecuta la operacion costosa (~300ms)
  GET /slow-cached   -> primera vez ~300ms, siguientes veces (dentro
                        de la ventana de expiracion) responde desde
                        Redis en unos pocos ms

El objetivo es reproducir, en miniatura, el flujo de diagnostico del
post: medir tiempos de respuesta -> detectar el cuello de botella ->
aplicar caching -> volver a medir y confirmar la mejora.
"""

import time
import json
from functools import wraps
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import redis

redis_client = redis.Redis(host="redis", port=6379, db=0)


def cache(expire=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f.__name__ + str(args) + str(kwargs)
            result = redis_client.get(key)
            if result:
                return json.loads(result.decode("utf-8"))
            result = f(*args, **kwargs)
            redis_client.setex(key, expire, json.dumps(result))
            return result

        return decorated_function

    return decorator


def expensive_operation(param):
    # Simula una operacion costosa: query pesada, calculo, llamada externa, etc.
    time.sleep(0.3)
    return {"param": param, "computed_at": time.time()}


@cache(expire=30)
def expensive_operation_cached(param):
    time.sleep(0.3)
    return {"param": param, "computed_at": time.time()}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silenciar logs de acceso, el benchmark ya reporta tiempos

    def _send_json(self, payload, elapsed_ms):
        body = json.dumps({**payload, "elapsed_ms": round(elapsed_ms, 1)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        start = time.perf_counter()

        if self.path.startswith("/slow-cached"):
            result = expensive_operation_cached("demo")
        elif self.path.startswith("/slow"):
            result = expensive_operation("demo")
        elif self.path == "/health":
            self._send_json({"status": "ok"}, 0)
            return
        else:
            self.send_response(404)
            self.end_headers()
            return

        elapsed_ms = (time.perf_counter() - start) * 1000
        self._send_json(result, elapsed_ms)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("Demo app escuchando en :8080")
    server.serve_forever()
