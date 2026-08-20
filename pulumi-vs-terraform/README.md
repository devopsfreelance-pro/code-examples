# Pulumi vs Terraform: mismo recurso, dos herramientas

Post: https://www.devopsfreelance.pro/blog/posts/pulumi-vs-terraform/

## Qué demuestra este ejemplo

El post compara Terraform (HCL declarativo) contra Pulumi (Python, .NET, Go,
etc.) usando como ejemplo una instancia EC2 idéntica definida en ambas
herramientas. Este ejemplo replica esa misma idea pero sin depender de una
cuenta de AWS: levanta **el mismo contenedor nginx** una vez con Terraform
(`terraform/main.tf`, provider `kreuzwerker/docker`) y otra vez con Pulumi en
Python (`pulumi/__main__.py`, paquete `pulumi_docker`), para que puedas
comparar en minutos:

- Sintaxis declarativa (HCL) vs código Python real (variables, tipos,
  f-strings) para definir el mismo recurso.
- Cómo cada herramienta maneja outputs/exports (`output` en Terraform,
  `pulumi.export` en Pulumi).
- El flujo de comandos de cada una: `init/plan/apply` vs `pulumi up`.

No reproduce todo el post (testing, CI/CD, migración): eso queda como lectura,
esto es para tocar la diferencia de sintaxis con las manos.

## Requisitos

- Docker corriendo localmente (`docker info` debe funcionar).
- Terraform >= 1.5 (`terraform version`).
- Pulumi CLI >= 3.0 (`pulumi version`) — instalación: https://www.pulumi.com/docs/install/
- Python 3.9+ y `pip`.
- No hace falta cuenta de AWS. Pulumi sí requiere una cuenta gratuita
  (pulumi.com) o backend local (`pulumi login --local`) para guardar el
  estado del stack; el ejemplo usa backend local, sin login.

## Pasos para correrlo

### 1. Terraform

```bash
cd terraform
terraform init
terraform apply -auto-approve
```

Salida esperada (resumen):

```
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

container_id = "..."
url = "http://localhost:8081"
```

Verificar:

```bash
curl -s http://localhost:8081 | grep -i "Welcome to nginx"
```

Limpiar:

```bash
terraform destroy -auto-approve
```

### 2. Pulumi (Python)

```bash
cd pulumi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

pulumi login --local
pulumi stack init dev
pulumi up --yes
```

Salida esperada (resumen):

```
Outputs:
    container_id: "..."
    url          : "http://localhost:8082"

Resources:
    + 3 created
```

Verificar:

```bash
curl -s http://localhost:8082 | grep -i "Welcome to nginx"
```

Limpiar:

```bash
pulumi destroy --yes
pulumi stack rm dev --yes
deactivate
```

## Notas

- Los puertos son distintos a propósito (8081 Terraform, 8082 Pulumi) para
  poder correr ambos ejemplos al mismo tiempo sin conflicto.
- `pulumi login --local` guarda el estado del stack en
  `~/.pulumi/` en vez de en el servicio SaaS de Pulumi (equivalente
  aproximado a un backend local de Terraform, sin credenciales externas).
- Compará el tamaño y forma de `terraform/main.tf` contra `pulumi/__main__.py`:
  mismo resultado, dos paradigmas — el punto central del post.
