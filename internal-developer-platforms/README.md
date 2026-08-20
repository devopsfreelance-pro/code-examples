# Internal Developer Platform: mini golden path ejecutable

Ejemplo de código para el post del blog: [Guía Completa de Internal developer platforms](https://www.devopsfreelance.pro/blog/posts/internal-developer-platforms/)

## Qué demuestra

El post explica que una internal platform (IDP) le da al developer una interfaz simple que oculta la complejidad de Kubernetes, y muestra como ejemplo un spec `WebApplication` que un developer completaría en vez de escribir a mano un Deployment, un Service y un Ingress. Este directorio implementa esa misma idea de punta a punta y en miniatura:

1. `platform-spec.yaml` es el spec de autoservicio que "pide" el developer (mismo formato `WebApplication` del post: imagen, réplicas, recursos, puerto).
2. `translate.py` es la capa de orquestación de la plataforma: valida el spec y lo traduce a los `values` de un Helm chart real. El developer nunca ve Helm ni Kubernetes.
3. `chart/` es el chart interno que la plataforma mantiene, con buenas prácticas ya incorporadas por defecto (resource requests, readiness/liveness probes) tal como describe la sección "La implementación técnica debe priorizar la simplicidad y la reutilización de herramientas existentes".
4. `deploy.sh` simula el botón "Deploy" de la plataforma: crea un cluster local, corre la traducción, despliega con Helm y prueba la app resultante.

En una IDP real esto vive detrás de un portal (Backstage, un CLI propio, etc.); acá se corre localmente para poder ver el flujo completo funcionando en minutos, sin necesitar Backstage ni un cluster cloud.

## Requisitos

- Docker (para que `kind` pueda levantar el cluster)
- [`kind`](https://kind.sigs.k8s.io/) (Kubernetes in Docker)
- `kubectl`
- `helm` (v3)
- Python 3.8+ con `pyyaml` (`pip install pyyaml`)

## Cómo correrlo

```bash
cd internal-developer-platforms

# 1. Ver el spec de autoservicio que "pide" el developer
cat platform-spec.yaml

# 2. (opcional) Ver a qué lo traduce la plataforma, sin desplegar nada
python3 translate.py platform-spec.yaml

# 3. Desplegar de punta a punta: crea el cluster kind, traduce el spec,
#    instala el chart con Helm, espera a que el pod esté listo y prueba
#    la app con curl vía port-forward
./deploy.sh
```

Al terminar la prueba, el port-forward queda corriendo hasta que cortes con `Ctrl+C`. Para limpiar todo:

```bash
kind delete cluster --name idp-demo
```

### Salida esperada

Al correr `python3 translate.py platform-spec.yaml`:

```yaml
name: mi-aplicacion
image: nginxdemos/hello:latest
replicas: 2
port: 80
resources:
  requests:
    cpu: 100m
    memory: 128Mi
```

Al correr `./deploy.sh`, entre otras líneas verás:

```
==> Creando cluster kind 'idp-demo'
==> Traduciendo platform-spec.yaml a valores de Helm
==> Desplegando WebApplication via Helm
==> Esperando a que el Deployment este listo
deployment "mi-aplicacion" successfully rolled out
==> Port-forward a localhost:8080 (Ctrl+C para cortar)
==> Probando la aplicacion desplegada
Server address: 10.244.0.6:80
Server name: mi-aplicacion-xxxxxxxxxx-xxxxx
...
==> OK. La app quedo corriendo en el cluster kind 'idp-demo'.
```

La imagen usada (`nginxdemos/hello`) responde con una página HTML simple que confirma qué pod la sirvió, útil para ver a simple vista que el `replicas: 2` del spec se tradujo en pods reales balanceados por el Service.

## Qué queda fuera de este mini-ejemplo

Para mantenerlo chico y ejecutable en minutos sin dependencias pagas, no se implementa el catálogo de servicios (tipo Backstage), el `Ingress` con TLS, la base de datos declarada en el ejemplo del post ni la capa de gobernanza/costos. La idea es aislar el concepto central: **spec simple → plataforma traduce → recursos reales de Kubernetes con buenas prácticas por defecto**.
