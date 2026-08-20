# Nginx Reverse Proxy para microservicios

Ejemplo del post: [Nginx Reverse Proxy: Arquitectura escalable para microservicios](https://www.devopsfreelance.pro/blog/posts/nginx-microservicios/)

## Qué demuestra

Un nginx reverse proxy en frente de dos microservicios simulados (`usuarios` y `pedidos`), ilustrando los conceptos centrales del post:

- **Enrutamiento por path** hacia distintos servicios backend (patrón API gateway centralizado).
- **Balanceo de carga** round-robin (el default de nginx) entre dos instancias del servicio `usuarios`.
- **Rate limiting** con `limit_req_zone` (10 req/s por IP, con burst).
- **Health check pasivo**: si una instancia falla, nginx la saca de la rotación (`proxy_next_upstream`).
- **Logs estructurados** que incluyen el backend upstream usado y el tiempo de respuesta.

Cada backend responde con su propio nombre de instancia en el JSON, así que al pegarle varias veces al mismo endpoint se ve cómo nginx alterna entre las instancias `backend-a-1` y `backend-a-2`.

## Requisitos

- Docker y Docker Compose (`docker compose version`)

## Cómo correrlo

```bash
cd nginx-microservicios
docker compose up --build
```

Esperá a ver en los logs que las tres instancias backend y nginx arrancaron. En otra terminal:

```bash
# Pegarle varias veces al servicio de usuarios: alterna entre backend-a-1 y backend-a-2
for i in $(seq 1 6); do curl -s http://localhost:8080/usuarios/perfil; echo; done

# Servicio de pedidos: siempre responde backend-b-1 (una sola instancia)
curl -s http://localhost:8080/pedidos/123; echo

# Ver el estado interno de nginx
curl -s http://localhost:8080/nginx-status
```

Para probar el rate limiting (10 req/s, burst 5), disparar muchas requests rápido:

```bash
for i in $(seq 1 30); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/usuarios/perfil; done
```

Vas a ver algunos `200` y, al superar el límite, respuestas `503` (Service Unavailable, generado por nginx cuando corta por rate limit).

Para cortar todo:

```bash
docker compose down
```

## Salida esperada

Al pegarle a `/usuarios/perfil` en un loop, vas a ver alternancia entre instancias, por ejemplo:

```
{"instancia": "backend-a-1", "path": "/perfil"}
{"instancia": "backend-a-2", "path": "/perfil"}
{"instancia": "backend-a-1", "path": "/perfil"}
{"instancia": "backend-a-2", "path": "/perfil"}
```

Al pegarle a `/pedidos/123`, siempre la misma instancia (solo hay una):

```
{"instancia": "backend-b-1", "path": "/123"}
```

En los logs de nginx (`docker compose logs nginx`) vas a ver líneas con el backend upstream elegido en cada request, por ejemplo:

```
nginx-1  | 172.19.0.1 - [20/Aug/2026:15:00:01 +0000] "GET /usuarios/perfil HTTP/1.1" upstream=172.19.0.3:8000 status=200 rt=0.002
```

## Estructura

```
nginx-microservicios/
├── docker-compose.yml   # nginx + 3 instancias de un backend simulado
├── nginx.conf            # reverse proxy, upstreams, balanceo, rate limiting
└── backend/
    ├── Dockerfile
    └── app.py             # servidor HTTP mínimo que devuelve su nombre de instancia
```
