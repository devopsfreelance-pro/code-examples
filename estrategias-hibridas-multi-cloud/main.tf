# Ejemplo de estrategia hibrida: un mismo flujo de Terraform provisiona
# un recurso "cloud" (S3 en LocalStack, emulando AWS) y un recurso
# "on-premise" (un contenedor Docker local), demostrando la capa de
# abstraccion/IaC agnostica al proveedor descrita en el post.

# --- Proveedor "cloud" (AWS, apuntado a LocalStack) ---
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3 = "http://localhost:4566"
  }
}

# --- Proveedor "on-premise" (Docker local, simula el datacenter propio) ---
provider "docker" {}

# Recurso en la "nube": bucket S3 para almacenamiento de artefactos
resource "aws_s3_bucket" "cloud_artifacts" {
  bucket = "hybrid-demo-cloud-artifacts"

  tags = {
    entorno   = "cloud"
    proveedor = "aws"
    proyecto  = "estrategias-hibridas-multi-cloud"
  }
}

# Recurso "on-premise": servicio web corriendo en infraestructura propia
resource "docker_image" "onprem_nginx" {
  name         = "nginx:1.27-alpine"
  keep_locally = true
}

resource "docker_container" "onprem_web" {
  name  = "hybrid-demo-onprem-web"
  image = docker_image.onprem_nginx.image_id

  ports {
    internal = 80
    external = 8080
  }

  labels {
    label = "entorno"
    value = "on-premise"
  }
}
