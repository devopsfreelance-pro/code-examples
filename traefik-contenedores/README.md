# Traefik Proxy: descubrimiento automático con Docker

Post: https://www.devopsfreelance.pro/blog/posts/traefik-contenedores/

## Qué demuestra este ejemplo

El post explica que la "magia" de Traefik es el **automatic discovery**: cuando
se integra con Docker, detecta contenedores nuevos por sus labels y crea
routers y services sin tocar ningún archivo de configuración ni reiniciar
nada. Este ejemplo reproduce exactamente eso en miniatura:

- `docker-compose.yml` levanta Traefik y dos servicios (`whoami-a`,
  `whoami-b`), cada uno enrutado por subdominio (`a.localhost`,
  `b.localhost`) solo con labels Docker, igual que el caso
  "frontend.localhost / api.localhost" que menciona el post.
- El dashboard de Traefik queda expuesto en un entrypoint separado
  (puerto 8899, no el 80 de tráfico) y protegido con `basicAuth`, siguiendo
  la recomendación de "Mejores Prácticas" del post de no exponerlo con
  `--api.insecure`.
- `scripts/demo.sh` levanta un tercer contenedor (`whoami-c`) **en caliente**
  con `docker run` y las labels correctas, y muestra que Traefik lo enruta
  solo, sin reiniciarse ni releer ningún archivo: eso es el descubrimiento
  automático en acción.

Fuera de alcance (no está en este mini-ejemplo): certificados Let's Encrypt,
`docker-socket-proxy`, Kubernetes/IngressRoute, rate limiting y el resto de
middlewares avanzados que menciona el post.

## Requisitos

- Docker con Docker Compose v2 (`docker compose version`)
- `curl`
- Puertos `80` y `8899` libres en tu máquina

No hace falta cuenta ni servicio externo: todo corre en local con imágenes
públicas (`traefik`, `traefik/whoami`).

## Cómo correrlo

### 1. Levantar Traefik y los dos servicios

```bash
cd traefik-contenedores
docker compose up -d
```

### 2. Probar el enrutamiento por subdominio

```bash
curl -H "Host: a.localhost" http://localhost/
curl -H "Host: b.localhost" http://localhost/
```

Salida esperada (el `Hostname` es el ID del contenedor, va a variar):

```
Hostname: ea7f67404c52
IP: 127.0.0.1
IP: ::1
IP: 172.19.0.3
RemoteAddr: 172.19.0.1:42040
GET / HTTP/1.1
Host: a.localhost
...
```

### 3. Ver el dashboard (protegido con basicAuth)

```bash
# Sin credenciales: 401
curl -o /dev/null -s -w "%{http_code}\n" -H "Host: dashboard.localhost" http://localhost:8899/dashboard/

# Con credenciales (admin / admin123): 200
curl -o /dev/null -s -w "%{http_code}\n" -u admin:admin123 -H "Host: dashboard.localhost" http://localhost:8899/dashboard/
```

También podés abrirlo en el navegador con un `Host` header vía
`http://dashboard.localhost:8899/dashboard/` si tenés `dashboard.localhost`
resuelto a `127.0.0.1` (en Linux/macOS `localhost` y sus subdominios ya
resuelven a loopback por defecto).

Usuario y contraseña son solo para este demo (`admin` / `admin123`, hash
generado con `openssl passwd -apr1 admin123`). Cambiá el hash en el label
`dashboard-auth.basicauth.users` del `docker-compose.yml` antes de usar esto
fuera de un entorno local descartable.

### 4. Ver el descubrimiento automático en vivo

```bash
bash scripts/demo.sh
```

Este script consulta `a.localhost` y `b.localhost`, después levanta un
contenedor `whoami-c` con `docker run` (labels incluidas, sin tocar
`docker-compose.yml`), espera unos segundos y muestra que `c.localhost` ya
responde. Al final limpia el contenedor de la demo.

Salida esperada (resumida):

```
== 1. Servicios a.localhost y b.localhost (ya definidos en docker-compose.yml) ==
Hostname: ea7f67404c52
...
== 2. Levantando whoami-c EN CALIENTE con 'docker run', sin editar compose ni reiniciar Traefik ==
Esperando a que Traefik detecte el nuevo contenedor (descubrimiento automático)...

== 3. c.localhost ya responde, sin haber tocado la configuración de Traefik ==
Hostname: 38f4c9ba147a
...
== 4. Limpieza del contenedor de la demo ==
Listo.
```

### 5. Apagar todo

```bash
docker compose down
```

## Notas

- Se usa `traefik:v3.7`. Con imágenes de Traefik más viejas (`v3.1`–`v3.5`)
  contra un daemon Docker reciente puede aparecer el error `client version
  1.24 is too old` al conectar por el socket: es un problema de negociación
  de versión de API entre el cliente Docker embebido en Traefik y daemons
  Docker modernos, no algo de este ejemplo. Si te pasa, subí la versión de
  la imagen de Traefik.
- El socket de Docker se monta en modo lectura (`:ro`). El post recomienda ir
  un paso más allá en producción y usar un `docker-socket-proxy` en lugar de
  montar el socket directo; queda fuera de este mini-ejemplo por simplicidad.
