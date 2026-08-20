# Podman: contenedor rootless + generacion de manifiesto Kubernetes

Ejemplo de codigo que acompaña al post [Podman: Alternativa Segura y Moderna a Docker en 2025](https://www.devopsfreelance.pro/blog/posts/podman-alternativa-a-docker/).

## Que demuestra

El post explica que la diferencia central entre Podman y Docker no es de
comandos (son casi identicos) sino de arquitectura: Podman no tiene un
demonio root (`dockerd`), y cada contenedor corre como proceso hijo directo
del usuario, aislado mediante *user namespaces* y *subordinate UIDs*
(rootless containers).

Este ejemplo pone eso en evidencia con una app minima:

1. Construye una imagen con un `Containerfile` (compatible con `docker build`
   y `podman build`, sin modificaciones).
2. Corre el contenedor en modo **rootless** con `podman run`.
3. Verifica, desde el host, que el proceso del contenedor corre con un UID
   sin privilegios (mapeo de subordinate UID), no con root real del host.
4. Genera un manifiesto de Kubernetes directamente desde el contenedor en
   ejecucion con `podman generate kube`, la capacidad que el post destaca
   como ventaja de Podman para pasar de desarrollo local a Kubernetes sin
   reescribir nada a mano.
5. Incluye un `compose.yml` para levantar el mismo servicio junto a Redis
   con `podman-compose`, mostrando que en Podman la red entre contenedores
   hay que declararla explicitamente (a diferencia de la red bridge
   automatica de Docker).

## Requisitos

- Linux (rootless containers usa user namespaces del kernel Linux; en
  macOS/Windows Podman funciona pero corre dentro de una VM y el paso 3
  del demo no aplica igual).
- [Podman](https://podman.io/docs/installation) instalado:

  ```bash
  # Fedora / RHEL / CentOS Stream
  sudo dnf install podman

  # Ubuntu / Debian
  sudo apt-get update
  sudo apt-get install podman
  ```

- `curl` (para probar el endpoint; opcional, el script sigue si no esta).
- Opcional, para el paso de Compose: `podman-compose`

  ```bash
  # Via pip (cualquier distro con Python 3)
  pip3 install --user podman-compose
  ```

No hace falta Docker instalado; todo corre con Podman.

## Pasos para correrlo

### 1. Build + run rootless + generate kube (script principal)

```bash
cd podman-alternativa-a-docker
chmod +x demo.sh
./demo.sh
```

Salida esperada (resumida):

```
==> 1) Construyendo la imagen con Podman (equivalente a docker build)
...
==> 2) Corriendo el contenedor en modo rootless
<container id>

==> 3) UID del proceso visto desde el HOST (fuera del contenedor)
    Deberia ser un UID sin privilegios (no 0), aunque adentro el proceso se vea como root/UID configurado.
HUSER    PID    COMMAND
1000     12345  python

==> 4) Probando el servicio
Hola desde un contenedor rootless con Podman
hostname: <hash>
PID dentro del contenedor: 1
UID dentro del contenedor: 1000
GID dentro del contenedor: 1000

==> 5) Generando manifiesto de Kubernetes desde el contenedor en ejecucion
    Manifiesto guardado en podman-kube.yaml

==> 6) Limpieza
    Contenedor detenido y eliminado. La imagen 'podman-demo:latest' y el archivo podman-kube.yaml quedan disponibles.
```

El campo clave es `HUSER` en el paso 3: muestra el UID real en el host
(por ejemplo `1000`, tu propio usuario), nunca `0`/root, aunque el proceso
dentro del contenedor corre como el usuario `appuser` (UID 1000 dentro del
namespace del contenedor). Revisa `podman-kube.yaml` para ver el manifiesto
de Kubernetes generado automaticamente.

### 2. (Opcional) Levantar con podman-compose

```bash
podman-compose -f compose.yml up -d
curl -s http://localhost:8080/
podman-compose -f compose.yml down
```

Salida esperada del `curl`: el mismo texto de saludo del paso anterior. Esto
demuestra que `compose.yml` es intercambiable entre Docker Compose y
podman-compose, salvo por la red `appnet`, que aqui se declara de forma
explicita (con Podman no hay red bridge automatica entre servicios).

## Archivos

- `Containerfile` — imagen minima en Python, corre como usuario sin
  privilegios dentro del contenedor.
- `app/app.py` — servidor HTTP que reporta PID/UID para verificar el
  aislamiento rootless.
- `compose.yml` — definicion multi-servicio (web + redis) con red explicita
  para `podman-compose`.
- `demo.sh` — script que automatiza build, run rootless, verificacion de
  UID y `podman generate kube`.
