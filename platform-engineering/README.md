# Platform Engineering: mini IDP scaffolder (golden path)

Code example for the blog post: [Platform Engineering: What It Is and How to Build an IDP](https://www.devopsfreelance.pro/blog/en/posts/platform-engineering-guide/)

## What it demonstrates

The post explains that an Internal Developer Platform (IDP) gives developers a "golden path": instead of manually setting up the repo, CI/CD, Kubernetes manifests, monitoring, and catalog registration, they request a new service with a single command and the platform generates everything automatically (the "Example: Template for a New Service" section with the Backstage scaffolder illustrates exactly this).

`scaffold.py` is a minimal version of that same mechanism, without depending on Backstage or a cluster: a Python script that takes the service name (and optionally which database and cache it needs) and generates, from templates, the complete structure described in the post's "Structure of a Generated Service":

```
my-service/
├── src/                          # where the app code goes
├── Dockerfile                    # multi-stage, pre-configured
├── .github/workflows/ci-cd.yaml  # pipeline: build, test, push, update manifest
├── k8s/
│   ├── deployment.yaml           # with resource limits and probes
│   ├── service.yaml              # ClusterIP
│   ├── ingress.yaml              # with TLS via cert-manager
│   └── hpa.yaml                  # autoscaling
├── monitoring/
│   └── alerts.yaml               # PrometheusRule (error rate, pods down)
├── catalog-info.yaml             # catalog registration (Backstage-style)
└── docs/
    └── index.md                  # automatic TechDocs
```

It's the same principle as a Backstage Software Template (repo + CI/CD + infra + monitoring + catalog in minutes), reduced to a script that runs locally so you can see it working without spinning up a full portal.

## Requirements

- Python 3.8 or higher (standard library only, no dependencies to install)

## How to run it

```bash
cd platform-engineering

# Generate a service with database and cache
python3 scaffold.py --name orders-api --owner payments-team --database postgresql --cache redis

# Generate a minimal service, without extra infrastructure
python3 scaffold.py --name notifications-api

# Generate into a different output directory
python3 scaffold.py --name billing-api --output /tmp/my-services
```

### Expected output

```
Generando servicio 'orders-api' (owner=payments-team, database=postgresql, cache=redis)

  creado  orders-api/Dockerfile
  creado  orders-api/.github/workflows/ci-cd.yaml
  creado  orders-api/k8s/deployment.yaml
  creado  orders-api/k8s/service.yaml
  creado  orders-api/k8s/ingress.yaml
  creado  orders-api/k8s/hpa.yaml
  creado  orders-api/monitoring/alerts.yaml
  creado  orders-api/catalog-info.yaml
  creado  orders-api/docs/index.md
  creado  orders-api/src/ (codigo de la app va aca)

Listo. Servicio 'orders-api' generado en: /ruta/completa/orders-api
Proximos pasos: 'cd', inicializar git, hacer push y dejar que CI/CD tome el resto.
```

Afterward you can inspect any of the generated files, for example:

```bash
cat orders-api/k8s/deployment.yaml
cat orders-api/catalog-info.yaml
```

### Included validations

The script validates the same things a real Backstage template would validate before creating anything:

```bash
# Invalid name (doesn't match ^[a-z0-9-]+$) -> error, no files created
python3 scaffold.py --name Mi_Servicio

# Directory already exists -> error, won't overwrite
python3 scaffold.py --name orders-api   # if you already ran the example above
```

## How to extend it

- Add a real `terraform:apply` (like the `create-infra` step of the Backstage template in the post) replacing the placeholder in `.github/workflows/ci-cd.yaml`.
- Add a new template in `templates/` (for example `dashboard.json.tmpl` for Grafana) and register it in the `mapping` dictionary in `scaffold.py`.
- Connect it to a real catalog (Backstage, Port, Cortex) by POSTing the generated `catalog-info.yaml` to its API instead of just writing it to disk.

## Notes

- It doesn't include real credentials or accounts: `registry.example.com` and `example.com` are intentional domain placeholders (not secrets), meant to be replaced with your real registry/domain.
- It doesn't require Docker, Kubernetes, or GitHub Actions to try it out: the generated files are valid (parseable YAML) but aren't executed as part of this example.

---

## 🇪🇸 Versión en español

# Platform Engineering: mini IDP scaffolder (golden path)

Ejemplo de código para el post del blog: [Platform Engineering: Qué Es, Por Qué Importa y Cómo Implementarlo](https://www.devopsfreelance.pro/blog/posts/platform-engineering/)

## Qué demuestra

El post explica que una Internal Developer Platform (IDP) le da al developer un "golden path": en vez de armar a mano el repo, el CI/CD, los manifests de Kubernetes, el monitoreo y el registro en el catálogo, pide un servicio nuevo con un solo comando y la plataforma genera todo automáticamente (la sección "Ejemplo: Template para Nuevo Servicio" con Backstage scaffolder ilustra exactamente esto).

`scaffold.py` es una versión mínima de ese mismo mecanismo, sin depender de Backstage ni de un cluster: un script en Python que toma el nombre del servicio (y opcionalmente qué base de datos y cache necesita) y genera, a partir de templates, la estructura completa que describe el post en "Estructura de un Servicio Generado":

```
mi-servicio/
├── src/                          # donde va el código de la app
├── Dockerfile                    # multi-stage, pre-configurado
├── .github/workflows/ci-cd.yaml  # pipeline: build, test, push, actualizar manifest
├── k8s/
│   ├── deployment.yaml           # con resource limits y probes
│   ├── service.yaml              # ClusterIP
│   ├── ingress.yaml              # con TLS vía cert-manager
│   └── hpa.yaml                  # autoescalado
├── monitoring/
│   └── alerts.yaml               # PrometheusRule (error rate, pods caídos)
├── catalog-info.yaml             # registro en el catálogo (estilo Backstage)
└── docs/
    └── index.md                  # TechDocs automáticos
```

Es el mismo principio que un Software Template de Backstage (repo + CI/CD + infra + monitoreo + catálogo en minutos), reducido a un script que corre localmente para poder verlo funcionar sin levantar un portal completo.

## Requisitos

- Python 3.8 o superior (solo librería estándar, sin dependencias que instalar)

## Cómo correrlo

```bash
cd platform-engineering

# Generar un servicio con base de datos y cache
python3 scaffold.py --name orders-api --owner payments-team --database postgresql --cache redis

# Generar un servicio mínimo, sin infraestructura adicional
python3 scaffold.py --name notifications-api

# Generar en otro directorio de salida
python3 scaffold.py --name billing-api --output /tmp/mis-servicios
```

### Salida esperada

```
Generando servicio 'orders-api' (owner=payments-team, database=postgresql, cache=redis)

  creado  orders-api/Dockerfile
  creado  orders-api/.github/workflows/ci-cd.yaml
  creado  orders-api/k8s/deployment.yaml
  creado  orders-api/k8s/service.yaml
  creado  orders-api/k8s/ingress.yaml
  creado  orders-api/k8s/hpa.yaml
  creado  orders-api/monitoring/alerts.yaml
  creado  orders-api/catalog-info.yaml
  creado  orders-api/docs/index.md
  creado  orders-api/src/ (codigo de la app va aca)

Listo. Servicio 'orders-api' generado en: /ruta/completa/orders-api
Proximos pasos: 'cd', inicializar git, hacer push y dejar que CI/CD tome el resto.
```

Después podés inspeccionar cualquiera de los archivos generados, por ejemplo:

```bash
cat orders-api/k8s/deployment.yaml
cat orders-api/catalog-info.yaml
```

### Validaciones incluidas

El script valida lo mismo que validaría un template real de Backstage antes de crear nada:

```bash
# Nombre inválido (no cumple ^[a-z0-9-]+$) -> error, no crea archivos
python3 scaffold.py --name Mi_Servicio

# Directorio ya existente -> error, no sobreescribe
python3 scaffold.py --name orders-api   # si ya corriste el ejemplo de arriba
```

## Cómo extenderlo

- Agregar un `terraform:apply` real (como el paso `create-infra` del template de Backstage en el post) reemplazando el placeholder en `.github/workflows/ci-cd.yaml`.
- Sumar un template nuevo en `templates/` (por ejemplo `dashboard.json.tmpl` para Grafana) y agregarlo al diccionario `mapping` en `scaffold.py`.
- Conectarlo a un catálogo real (Backstage, Port, Cortex) haciendo un POST del `catalog-info.yaml` generado a su API en vez de solo escribirlo en disco.

## Notas

- No incluye credenciales ni cuentas reales: `registry.example.com` y `example.com` son placeholders de dominio intencionales (no secretos), pensados para reemplazar por tu registry/dominio real.
- No requiere Docker, Kubernetes ni GitHub Actions para probarlo: los archivos generados son válidos (YAML parseable) pero no se ejecutan como parte de este ejemplo.
