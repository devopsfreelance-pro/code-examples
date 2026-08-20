# Terraform Avanzado: módulos reutilizables + estado separado por entorno

Post: https://www.devopsfreelance.pro/blog/posts/terraform-avanzado/

## Qué demuestra este ejemplo

El post describe tres pilares del "Terraform avanzado" empresarial: estado
remoto separado por entorno/componente, módulos reutilizables con interfaces
tipadas y validadas, y gestión de múltiples entornos (dev/staging/production)
consumiendo el mismo módulo con distintos parámetros.

Este ejemplo aplica esos tres pilares a escala mínima, corriendo 100% local:

- **Un módulo reutilizable** (`modules/app_stack`) con variables tipadas,
  bloques `validation` (entorno debe ser `dev`/`staging`/`production`,
  `max_capacity >= min_capacity`) y tags combinados con `merge()`, igual que
  el bloque `module "application_infrastructure"` del post.
- **Dos entornos independientes** (`environments/dev` y
  `environments/prod`), cada uno con su propio backend (`backend "local"`
  apuntando a un archivo de estado distinto: `dev.tfstate` / `prod.tfstate`),
  igual que la estructura de directorios `environments/production/`,
  `environments/staging/` del post. Cada entorno invoca el mismo módulo con
  valores distintos (capacidad, tipo de instancia, backup).

Para que corra sin cuenta de nube ni Docker, el módulo no crea recursos AWS
reales: usa el provider `local` (built-in de Terraform) para escribir un
archivo JSON que representa la infraestructura que se hubiera creado. La
lógica de módulos, validación y separación de estado es idéntica a un caso
real con backend S3 + DynamoDB.

## Requisitos

- Terraform >= 1.5 (`terraform version`)

No hace falta Docker, AWS ni credenciales: todo corre local.

## Pasos para correrlo

1. Entrar al entorno `dev` e inicializar:

   ```bash
   cd environments/dev
   terraform init
   ```

2. Ver el plan y aplicar:

   ```bash
   terraform plan
   terraform apply -auto-approve
   ```

3. Ver los outputs y el archivo generado:

   ```bash
   terraform output
   cat output/dev-api-gateway.json
   ```

4. Repetir en `production` (estado completamente separado del de dev):

   ```bash
   cd ../prod
   terraform init
   terraform apply -auto-approve
   terraform output
   cat output/production-api-gateway.json
   ```

5. Comprobar la validación de variables (debe fallar con un mensaje claro):

   ```bash
   terraform apply -var='environment=qa' -auto-approve
   ```

6. Limpiar todo al terminar:

   ```bash
   cd ../dev && terraform destroy -auto-approve
   cd ../prod && terraform destroy -auto-approve
   ```

## Salida esperada

Después del `apply` en `dev` (paso 2-3):

```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

applied_tags = {
  "Component" = "api-gateway"
  "ManagedBy" = "terraform"
  "Module" = "app_stack"
  "Tier" = "application"
}
capacity_range = "1-2"
config_path = "./output/dev-api-gateway.json"
```

En `production` (paso 4) `capacity_range` va a ser `"3-10"` y el JSON va a
tener `"enable_backup": true` y `"backup_retention": 30`, mientras que en
`dev` `enable_backup` es `false` y `backup_retention` sale en `0`: son los
mismos valores que distingue el post entre entornos.

El paso 5 falla así, mostrando la validación del módulo:

```
Error: Invalid value for variable

  on main.tf line X:
  ...

El entorno debe ser dev, staging o production.
```

## Notas

- `dev.tfstate` y `prod.tfstate` quedan en cada carpeta de entorno (backend
  local): en un caso real serían dos keys distintas en el mismo bucket S3
  (`dev/infrastructure/terraform.tfstate`, `production/infrastructure/terraform.tfstate`),
  tal como muestra el bloque `backend "s3"` del post. La mecánica de
  aislamiento de estado es la misma.
- El directorio `output/` se genera al aplicar y no debe commitearse (son
  artefactos locales de la corrida).
- Este ejemplo no cubre Terraform Cloud/Enterprise, Sentinel/OPA ni el
  pipeline de GitLab CI que menciona el post: esas piezas requieren una
  cuenta o runner real y el post ya las explica en detalle conceptual.
