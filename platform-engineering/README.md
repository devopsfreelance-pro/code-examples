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
