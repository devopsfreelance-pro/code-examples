# OpenTofu: módulos reutilizables y estado local

Ejemplo mínimo del post [OpenTofu: La alternativa open source a Terraform en 2026](https://www.devopsfreelance.pro/blog/posts/opentofu-alternativa-a-terraform/).

## Qué demuestra

El post explica que OpenTofu es un fork 100% open source (MPL 2.0) de Terraform, compatible con providers existentes, y muestra un ejemplo de módulo reutilizable `microservicio` para provisionar servicios con configuración de métricas.

Este ejemplo reproduce esa idea de forma ejecutable en tu máquina, sin necesidad de cuenta cloud: un módulo `modules/microservicio` se instancia dos veces (`api-usuarios` y `api-pagos`) con distintos parámetros (réplicas, métricas habilitadas). Cada instancia "provisiona" un recurso (aquí, un archivo JSON local en vez de un `aws_ecs_service` o `kubernetes_deployment` real) para que puedas ver en segundos:

- Cómo se usa `tofu init` / `tofu plan` / `tofu apply` / `tofu destroy`.
- Cómo un mismo módulo se reutiliza con distinta configuración por servicio.
- Cómo OpenTofu gestiona el estado (`terraform.tfstate`) para saber qué existe y aplicar solo los cambios necesarios.

No requiere AWS, Azure ni GCP: usa el provider `local` (parte del registro estándar de providers, gratuito).

## Requisitos

- [OpenTofu](https://opentofu.org/docs/intro/install/) instalado (`tofu version`). Instalación rápida en Linux:
  ```bash
  curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh
  chmod +x install-opentofu.sh
  ./install-opentofu.sh --install-method standalone
  ```

## Cómo correrlo

```bash
cd opentofu-alternativa-a-terraform

# Descarga el provider "local" y prepara el directorio de trabajo
tofu init

# Muestra el plan: 2 recursos a crear (uno por microservicio)
tofu plan

# Aplica el plan
tofu apply -auto-approve

# Inspecciona los archivos "provisionados"
cat output/api-usuarios.json
cat output/api-pagos.json

# Limpieza
tofu destroy -auto-approve
```

## Salida esperada

Tras `tofu apply -auto-approve`:

```
Plan: 2 to add, 0 to change, 0 to destroy.
...
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

servicios_generados = [
  "modules/microservicio/../../output/api-usuarios.json",
  "modules/microservicio/../../output/api-pagos.json",
]
```

Y el contenido de `output/api-usuarios.json`:

```json
{"habilitar_metricas":true,"managed_by":"OpenTofu","puerto_metricas":9090,"replicas":3,"servicio":"api-usuarios"}
```

`output/api-pagos.json` queda con `replicas: 2` y `habilitar_metricas: false` (sin puerto de métricas), mostrando que el mismo módulo produce resultados distintos según los parámetros de cada instancia.

## Estructura

```
opentofu-alternativa-a-terraform/
├── main.tf                       # Raíz: instancia el módulo dos veces
└── modules/
    └── microservicio/
        └── main.tf                # Módulo reutilizable (variables + recurso)
```
