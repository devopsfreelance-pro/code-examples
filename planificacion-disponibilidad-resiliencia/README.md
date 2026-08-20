# Alta disponibilidad y failover automatico con Nginx

Ejemplo de codigo para el post [Planificación de disponibilidad y resiliencia: Estrategia](https://www.devopsfreelance.pro/blog/posts/planificacion-disponibilidad-resiliencia/) del blog DevOps Freelance Pro.

## Que demuestra

El post habla de varios principios de resiliencia (eliminacion de puntos unicos
de fallo, redundancia, failover, degradacion elegante). Este ejemplo aterriza
el mas fundamental de todos con algo que corre en minutos en tu maquina:

- Dos instancias identicas de un mismo servicio (`web1` y `web2`), es decir,
  **redundancia** en lugar de un unico punto de fallo.
- Un balanceador Nginx delante de ambas, que reparte trafico y usa
  `max_fails` / `fail_timeout` (failover pasivo, similar en espiritu a un
  circuit breaker) para dejar de enviar trafico a una instancia que empieza
  a fallar.
- Un script que tumba una instancia en caliente y muestra que el sistema
  sigue respondiendo sin downtime visible para el cliente, sirviendo todo
  el trafico desde la instancia sana.

No reemplaza a un load balancer productivo (ALB, HAProxy con checks activos,
Envoy, etc.), pero ilustra el mecanismo exacto que esas herramientas
implementan a mayor escala.

## Requisitos

- Docker y Docker Compose (plugin `docker compose`, no el binario viejo `docker-compose`)
- `curl`
- Puerto `8080` libre en tu maquina

## Pasos para correrlo

1. Pararse en esta carpeta y levantar el stack:

   ```bash
   docker compose up -d --build
   ```

2. Esperar unos segundos a que los healthchecks pasen y confirmar que las
   dos instancias estan activas:

   ```bash
   docker compose ps
   ```

3. Probar manualmente que el balanceador alterna entre ambas instancias:

   ```bash
   for i in $(seq 1 6); do curl -s http://localhost:8080; done
   ```

   Salida esperada (el orden puede variar):

   ```
   Hola desde web1
   Hola desde web2
   Hola desde web1
   Hola desde web2
   Hola desde web1
   Hola desde web2
   ```

4. Correr la demo de resiliencia completa (tumba `web1`, muestra que el
   trafico sigue sirviendose desde `web2`, y despues restaura `web1`):

   ```bash
   chmod +x test-resilience.sh
   ./test-resilience.sh
   ```

   Salida esperada en el paso 3 del script (despues de parar `web1`):

   ```
   Hola desde web2  (request 1)
   Hola desde web2  (request 2)
   Hola desde web2  (request 3)
   Hola desde web2  (request 4)
   Hola desde web2  (request 5)
   Hola desde web2  (request 6)
   ```

5. (Opcional) Simular una falla de aplicacion sin tumbar el contenedor,
   usando el endpoint `/toggle` para que una instancia se reporte no-sana
   en su propio healthcheck:

   ```bash
   docker compose exec web1 python -c "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://localhost:8000/toggle', method='POST'))"
   ```

   Despues de el `fail_timeout` (10s) configurado en `nginx/nginx.conf`,
   Nginx deja de enviarle trafico a esa instancia hasta que vuelva a
   reportarse sana.

6. Apagar todo:

   ```bash
   docker compose down
   ```

## Estructura

```
planificacion-disponibilidad-resiliencia/
├── docker-compose.yml       # dos instancias + balanceador Nginx
├── nginx/nginx.conf         # upstream con failover pasivo (max_fails/fail_timeout)
├── app/
│   ├── app.py                # backend minimo: /, /health, /toggle
│   └── Dockerfile
└── test-resilience.sh       # demo automatizada de failover
```
