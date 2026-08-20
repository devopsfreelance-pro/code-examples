# HAProxy Load Balancing: runnable example

Post: [HAProxy Load Balancing: Complete Enterprise Guide](https://www.devopsfreelance.pro/blog/en/posts/haproxy-load-balancing-guide/)

## What this example demonstrates

A minimal local stack that illustrates the post's central concept: HAProxy as
a reverse proxy that distributes traffic across multiple backend servers with
active health checks.

- **Round-robin balancing** (`haproxy.cfg`, `backend web_servers` section): two
  Python servers (`web1`, `web2`) receive requests alternately. Each response
  includes the name of the backend that served it, so you can see the
  alternation live.
- **Active HTTP health checks**: HAProxy checks `GET /health` on each server
  every 2 seconds (`option httpchk`, `http-check expect status 200`). If a
  backend fails 2 checks in a row (`fall 2`) it's automatically taken out of
  rotation; it rejoins after 2 OK checks (`rise 2`), matching what the post
  describes in the high-availability section.
- **Real-time stats page** (`stats enable` on port `8404`), the same
  observability functionality the post mentions.

It doesn't include SSL/TLS termination, domain-based routing ACLs, or the
active-passive pair with Keepalived from the post (those would be overkill
for a mini example); the `balance` and `option httpchk` configuration is the
same syntax you'd use to add those features later.

## Requirements

- Docker and Docker Compose (`docker compose version`)
- Free ports on your machine: `8080` (traffic via HAProxy) and `8404` (stats)

## How to run it

```bash
cd haproxy-load-balancing
docker compose up --build
```

Wait to see `web1 escuchando en puerto 8080` and `web2 escuchando en puerto
8080` in the logs, and give it about 5 more seconds for HAProxy to confirm
the first health check on both servers (`inter 2s`, `rise 2`).

### 1. See the round-robin balancing

In another terminal:

```bash
for i in $(seq 1 6); do curl -s http://localhost:8080/; echo; done
```

Expected output (alternating `web1` and `web2`):

```
{"backend": "web1", "requests": 1}
{"backend": "web2", "requests": 1}
{"backend": "web1", "requests": 2}
{"backend": "web2", "requests": 2}
{"backend": "web1", "requests": 3}
{"backend": "web2", "requests": 3}
```

### 2. View the stats page

Open http://localhost:8404/stats . You'll see the `web_servers` table with
`web1` and `web2` in `UP` state (green), request rates, and response times.

### 3. Test failover (health checks)

Take down one of the backends to simulate a failure:

```bash
curl -s http://localhost:8080/toggle-health
```

Note: `/toggle-health` also goes through the load balancer, so it may hit
`web1` or `web2` depending on the round-robin turn. To target a specific
backend, use the container name directly:

```bash
docker compose exec web1 wget -qO- http://127.0.0.1:8080/toggle-health
```

Wait about 4-5 seconds (two check cycles) and refresh
http://localhost:8404/stats : `web1` will show up in red (`DOWN`). Meanwhile,
requests to `http://localhost:8080/` will always go to `web2` with no errors
for the client:

```bash
for i in $(seq 1 4); do curl -s http://localhost:8080/; echo; done
```

Bring it back with the same command (`toggle-health` toggles the state) and
within a few seconds it will show `UP` again and start receiving traffic.

### Stop the stack

```bash
docker compose down
```

---

# HAProxy Load Balancing: ejemplo ejecutable

## 🇪🇸 Versión en español

Post: [HAProxy: Guía completa de load balancing empresarial](https://www.devopsfreelance.pro/blog/posts/haproxy-load-balancing/)

## Qué demuestra este ejemplo

Un stack local minimo que ilustra el concepto central del post: HAProxy como
proxy reverso que distribuye trafico entre varios servidores backend con
health checks activos.

- **Balanceo roundrobin** (`haproxy.cfg`, sección `backend web_servers`): dos
  servidores Python (`web1`, `web2`) reciben peticiones de forma alternada.
  Cada respuesta incluye el nombre del backend que la atendió, así que se ve
  la alternancia en vivo.
- **Health checks HTTP activos**: HAProxy chequea `GET /health` en cada
  servidor cada 2 segundos (`option httpchk`, `http-check expect status 200`).
  Si un backend falla 2 chequeos seguidos (`fall 2`) se saca de rotación
  automáticamente; se reincorpora tras 2 chequeos OK (`rise 2`), igual que
  describe el post en la sección de alta disponibilidad.
- **Página de estadísticas en tiempo real** (`stats enable` en el puerto
  `8404`), la misma funcionalidad de observabilidad que menciona el post.

No incluye SSL/TLS termination, ACLs de enrutamiento por dominio, ni el par
activo-pasivo con Keepalived del post (serían overkill para un mini-ejemplo);
la configuración de `balance` y `option httpchk` es la misma sintaxis que
usarías para agregar esos features después.

## Requisitos

- Docker y Docker Compose (`docker compose version`)
- Puertos libres en tu máquina: `8080` (tráfico vía HAProxy) y `8404` (stats)

## Cómo correrlo

```bash
cd haproxy-load-balancing
docker compose up --build
```

Esperá a ver en los logs `web1 escuchando en puerto 8080` y `web2 escuchando
en puerto 8080`, y dale unos 5 segundos más para que HAProxy confirme el
primer health check de ambos servidores (`inter 2s`, `rise 2`).

### 1. Ver el balanceo roundrobin

En otra terminal:

```bash
for i in $(seq 1 6); do curl -s http://localhost:8080/; echo; done
```

Salida esperada (alternando `web1` y `web2`):

```
{"backend": "web1", "requests": 1}
{"backend": "web2", "requests": 1}
{"backend": "web1", "requests": 2}
{"backend": "web2", "requests": 2}
{"backend": "web1", "requests": 3}
{"backend": "web2", "requests": 3}
```

### 2. Ver la página de estadísticas

Abrí http://localhost:8404/stats . Vas a ver la tabla `web_servers` con
`web1` y `web2` en estado `UP` (verde), tasas de peticiones y tiempos de
respuesta.

### 3. Probar el failover (health checks)

Tirá abajo uno de los backends simulando una falla:

```bash
curl -s http://localhost:8080/toggle-health
```

Nota: `/toggle-health` también pasa por el balanceador, así que puede tocar
`web1` o `web2` según el turno de roundrobin. Para apuntar a un backend
específico, usá el nombre del contenedor directamente:

```bash
docker compose exec web1 wget -qO- http://127.0.0.1:8080/toggle-health
```

Esperá unos 4-5 segundos (dos ciclos de chequeo) y refrescá
http://localhost:8404/stats : `web1` va a aparecer en rojo (`DOWN`). Mientras
tanto, las peticiones a `http://localhost:8080/` van a ir siempre a `web2`
sin errores para el cliente:

```bash
for i in $(seq 1 4); do curl -s http://localhost:8080/; echo; done
```

Reactivalo con el mismo comando (`toggle-health` alterna el estado) y en unos
segundos vuelve a aparecer `UP` y a recibir tráfico.

### Apagar el stack

```bash
docker compose down
```
