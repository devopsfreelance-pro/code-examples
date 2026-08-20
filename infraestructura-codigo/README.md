# Infraestructura como Código: ciclo declarativo, estado y deriva

Post: https://www.devopsfreelance.pro/blog/posts/infraestructura-codigo/

## Qué demuestra este ejemplo

El post explica el ciclo central de la IaC: escribís una definición
declarativa del estado deseado, el motor la compara contra un **archivo de
estado**, genera un plan de las acciones necesarias y lo aplica. También
explica qué pasa cuando alguien modifica un recurso a mano por fuera de
Terraform (**deriva de configuración**, sección "Desafíos Reales") y cómo
`terraform plan` la detecta.

Este ejemplo reproduce ese ciclo completo corriendo 100% local, sin cuenta
cloud ni credenciales:

- `variables.tf` declara `environment` con una `validation` (debe ser
  `dev`, `staging` o `production`), igual que las validaciones tipadas que
  menciona el post para módulos reutilizables.
- `main.tf` declara un recurso `local_file` que representa, de forma
  declarativa, un "servidor web": no le decimos a Terraform cómo crearlo,
  solo qué propiedades debe tener el estado final (`environment`,
  `instance_type`). Usa el provider `local` (built-in de HashiCorp) en vez
  de `aws_db_instance` para no requerir credenciales de AWS; el mecanismo
  declarativo es idéntico al ejemplo del post.
- El backend es `local` (`terraform.tfstate` en esta misma carpeta): en
  producción sería un backend remoto como el bloque `backend "s3"` del
  post, pero el rol del archivo de estado como fuente de verdad es el
  mismo.
- El ejercicio de "editar el archivo a mano y correr `terraform plan`"
  reproduce la deriva de configuración que describe el post cuando alguien
  cambia algo por consola en vez de por código.

## Requisitos

- Terraform >= 1.5 (`terraform version`)

No hace falta Docker, AWS ni credenciales: todo corre local.

## Pasos para correrlo

1. Inicializar el proyecto (descarga el provider `local`):

   ```bash
   cd infraestructura-codigo
   terraform init
   ```

2. Ver el plan y aplicarlo:

   ```bash
   terraform plan
   terraform apply -auto-approve
   ```

3. Ver el archivo generado, que representa el recurso declarado:

   ```bash
   cat output/web-server.json
   ```

   Salida esperada:

   ```json
   {"environment":"dev","instance_type":"t3.micro","managed_by":"terraform","resource_type":"web_server"}
   ```

4. Simular una modificación manual por fuera de Terraform (deriva de
   configuración), como el ejemplo del ingeniero que cambia algo desde la
   consola web:

   ```bash
   echo '{"resource_type":"web_server","environment":"dev","instance_type":"CAMBIADO-A-MANO","managed_by":"nadie"}' > output/web-server.json
   terraform plan
   ```

   Terraform detecta que el archivo real ya no coincide con lo que registra
   el estado y propone recrearlo para volver a alinearlo con el código
   (`Plan: 1 to add, 0 to change, 0 to destroy`): esto es exactamente la
   detección de deriva que describe el post, solo que en vez de "1 to
   change" el provider `local` lo resuelve como recreación del archivo.

5. Aplicar de nuevo para corregir la deriva y volver al estado declarado en
   el código:

   ```bash
   terraform apply -auto-approve
   cat output/web-server.json
   ```

6. Comprobar la validación de variables (debe fallar con un mensaje claro,
   sin llegar a tocar el estado):

   ```bash
   terraform apply -auto-approve -var='environment=qa'
   ```

   Salida esperada:

   ```
   Error: Invalid value for variable
   ...
   El entorno debe ser dev, staging o production.
   ```

7. Limpiar todo al terminar:

   ```bash
   terraform destroy -auto-approve
   ```

## Notas

- `terraform.tfstate`, `.terraform/` y `output/` se generan al correr los
  comandos y no deben commitearse (son artefactos locales de la corrida).
  El `.terraform.lock.hcl` sí queda versionado, como en cualquier proyecto
  Terraform real.
- Este ejemplo no cubre backend remoto S3+DynamoDB, secretos con Vault/AWS
  Secrets Manager ni el pipeline de GitHub Actions que menciona el post:
  esas piezas requieren una cuenta cloud real y el post ya las explica en
  detalle conceptual con los mismos bloques HCL.
