# Self-service infrastructure: portal + gobernanza + aprovisionamiento

Post relacionado: [Guía Completa de Self-service infrastructure](https://www.devopsfreelance.pro/blog/posts/self-service-infrastructure/)

## Qué demuestra este ejemplo

El post describe cuatro capas que componen un sistema de autoservicio:
infraestructura base, abstracción/orquestación (Terraform, Pulumi,
Crossplane), control y gobernanza (OPA, políticas de la nube) e
infrastructure portal (donde el desarrollador declara lo que necesita, como
en el YAML `ServiceRequest` que muestra el artículo).

Este ejemplo reproduce ese flujo completo en tu máquina, sin nube ni
cuentas:

1. **Portal**: el desarrollador escribe una `ServiceRequest` declarativa
   (`service-request.yaml`), igual a la del post: plantilla, ambiente,
   tamaño de compute, base de datos e integraciones.
2. **Gobernanza**: `catalog.py` valida la solicitud contra el catálogo
   (plantillas y bases de datos permitidas) y contra una política de
   costos (qué tamaños de compute están autorizados por ambiente). Si algo
   no cumple, la solicitud se rechaza **antes** de tocar infraestructura.
3. **Orquestación**: `provision.py` traduce la solicitud aprobada a
   variables de Terraform (`terraform.tfvars.json`).
4. **Infraestructura**: Terraform "aprovisiona" el entorno. Para poder
   correrlo en minutos sin AWS/Azure/GCP, se usa el provider `local`
   (`main.tf`): cada recurso (cómputo, base de datos, monitoring, logging)
   se materializa como un archivo JSON en `output/`, y se genera un
   `environment-manifest.json` con el registro auditable de qué se
   provisionó, para quién y con qué configuración (la sección de
   "trazabilidad y auditoría" del post).

No repite el ejemplo de `politicas-codigo-opa-sentinel/` (que ya cubre OPA
evaluando un plan de Terraform) ni el de `platform-engineering/` (que ya
cubre el scaffolding de un servicio nuevo estilo Backstage): este ejemplo
se enfoca en el flujo end-to-end **solicitud declarativa → validación →
aprovisionamiento automático**, que es el hilo conductor del post.

## Requisitos

- Python 3.8 o superior con `pyyaml` (`pip install pyyaml`)
- Terraform >= 1.5 (no requiere cuenta de nube: usa el provider `local`,
  que se descarga solo en el `terraform init`)

## Cómo correrlo

```bash
cd self-service-infrastructure
pip install pyyaml

# 1. Solicitud valida: se aprueba y se aprovisiona
python3 provision.py service-request.yaml

# 2. Solicitud invalida (pide compute "xlarge" en development,
#    el catalogo solo permite small/medium): se rechaza sin tocar Terraform
python3 provision.py service-request-invalid.yaml
```

### Salida esperada (solicitud válida)

```
[portal] leyendo solicitud: service-request.yaml
[gobernanza] validando 'orders-api-dev' contra el catalogo...
[gobernanza] solicitud aprobada.
[orquestacion] generando variables de Terraform...
[orquestacion] escrito terraform.tfvars.json
[infraestructura] aprovisionando con Terraform...
...
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Listo. Entorno provisionado. Ver environment-manifest.json
```

Después de correrlo podés inspeccionar lo que se "provisionó":

```bash
cat environment-manifest.json
cat output/orders-api-dev/compute.json
cat output/orders-api-dev/database.json
cat output/orders-api-dev/monitoring.json
```

`environment-manifest.json` queda así (valores pueden variar si editás la
solicitud):

```json
{
  "service": "orders-api-dev",
  "owner": "payments-team",
  "environment": "development",
  "git_repository": "https://github.com/company/orders-api",
  "provisioned": {
    "compute": "250m CPU / 512Mi RAM",
    "database": "postgres 16 (shared)",
    "integrations": ["monitoring", "logging"]
  }
}
```

### Salida esperada (solicitud rechazada por gobernanza)

```
[portal] leyendo solicitud: service-request-invalid.yaml
[gobernanza] validando 'orders-api-dev' contra el catalogo...
[gobernanza] SOLICITUD RECHAZADA: compute 'xlarge' no esta permitido en environment 'development'. Permitidos: ['medium', 'small']
```

El script termina con código de salida `1` y no llega a ejecutar
`terraform apply`, tal como describe el post: la capa de control valida
"que las solicitudes cumplan con requisitos de seguridad, presupuesto y
cumplimiento normativo" antes de que se cree cualquier recurso.

### Limpiar lo generado

```bash
rm -rf output environment-manifest.json terraform.tfstate* .terraform terraform.tfvars.json
```

## Cómo extenderlo

- Agregar una plantilla nueva en `TEMPLATES` (`catalog.py`), por ejemplo
  `go-api`, y una regla de gobernanza asociada.
- Reemplazar el provider `local` de `main.tf` por providers reales de AWS
  (`aws_ecs_service`, `aws_db_instance`) manteniendo intacto el flujo
  portal → gobernanza → orquestación.
- Sumar una integración con Slack (como menciona el post) que dispare
  `provision.py` a partir de un comando, en vez de correrlo manualmente.

## Notas

- `https://github.com/company/orders-api` es un repositorio de ejemplo
  (placeholder de dominio, no una cuenta real): reemplazalo por tu propio
  repositorio si adaptás el ejemplo.
- Todo corre localmente: no se crea ninguna cuenta ni recurso en la nube.
