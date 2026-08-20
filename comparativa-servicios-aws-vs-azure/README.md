# AWS vs Azure vs GCP: misma infraestructura, tres sintaxis de Terraform

Post: [Guía completa: AWS vs Azure vs GCP - Comparativa 2025](https://www.devopsfreelance.pro/blog/posts/comparativa-servicios-aws-vs-azure/)

## Qué demuestra

El post compara servicio por servicio los tres proveedores (networking, storage,
bases de datos, etc.) mostrando fragmentos de Terraform para cada uno por separado.
Este ejemplo junta esos fragmentos en un único proyecto de Terraform **ejecutable**
que define la misma infraestructura mínima (red privada + almacenamiento de objetos
versionado) en los tres proveedores a la vez:

- `aws.tf` - VPC + subnet privada + bucket S3 con versionado.
- `azure.tf` - Resource Group + Virtual Network + subnet + Storage Account con
  replicación geo-redundante (GRS).
- `gcp.tf` - VPC + subnet privada + bucket de Cloud Storage con versionado.
- `versions.tf` - declara los tres providers (`aws`, `azurerm`, `google`) con
  credenciales ficticias, para poder inicializar y validar sin ninguna cuenta cloud
  real.

La idea es que abras los tres archivos lado a lado y veas de un vistazo cómo el
mismo concepto (red privada aislada + almacenamiento de objetos con versionado) se
expresa con nombres de recursos y atributos distintos en cada nube, tal como
plantea la sección "Comparativa Técnica Detallada de Servicios" del post.

No se aprovisiona nada real: el ejemplo se queda en `terraform validate`, que
revisa sintaxis y esquema de los recursos sin llamar a ninguna API de AWS, Azure
ni GCP. Por eso no hace falta cuenta ni credenciales de ningún proveedor.

## Requisitos

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.0
- Conexión a internet (para que `terraform init` descargue los tres providers la
  primera vez; no hace falta cuenta en ninguna nube)

## Cómo correrlo

1. Entrar al directorio del ejemplo:

```bash
cd comparativa-servicios-aws-vs-azure
```

2. Inicializar Terraform (descarga los providers de AWS, Azure y GCP):

```bash
terraform init -backend=false
```

Salida esperada (resumida):

```
Initializing provider plugins...
- Installing hashicorp/google v5.x.x...
- Installing hashicorp/aws v5.x.x...
- Installing hashicorp/azurerm v3.x.x...

Terraform has been successfully initialized!
```

3. Validar que los tres archivos son sintácticamente correctos y que los recursos
   usan los atributos esperados por cada provider:

```bash
terraform validate
```

Salida esperada:

```
Success! The configuration is valid.
```

4. Opcional: comparar el plan de cada proveedor por separado usando `-target` (el
   plan real fallará al intentar autenticarse contra la API, porque las
   credenciales en `versions.tf` son ficticias; para eso hace falta una cuenta
   real en cada nube, fuera del alcance de este mini-ejemplo):

```bash
terraform plan -target=aws_vpc.main -target=aws_s3_bucket.demo
```

5. Limpiar los archivos que genera `terraform init`:

```bash
rm -rf .terraform
```

## Notas sobre las credenciales ficticias

`versions.tf` configura los tres providers con valores inventados
(`fake-access-key`, `00000000-0000-0000-0000-000000000000`, `demo-project-id`,
etc.) y flags como `skip_credentials_validation` para que `terraform init` y
`terraform validate` funcionen sin tocar ninguna cuenta real. Si quisieras hacer
`terraform apply` de verdad, reemplazá esos valores por credenciales reales
(vía variables de entorno como `AWS_ACCESS_KEY_ID`, `ARM_CLIENT_ID` o
`GOOGLE_APPLICATION_CREDENTIALS`, nunca hardcodeadas en el `.tf`) y las
correspondientes al proveedor que quieras probar.

## Archivos

- `versions.tf` - declaración de providers y credenciales ficticias para validar
  sin cuenta real.
- `aws.tf` - VPC + subnet + bucket S3 versionado.
- `azure.tf` - Resource Group + VNet + subnet + Storage Account con GRS.
- `gcp.tf` - VPC + subnet + bucket de Cloud Storage versionado.
- `.terraform.lock.hcl` - lock file con las versiones exactas de providers usadas
  para validar este ejemplo.
