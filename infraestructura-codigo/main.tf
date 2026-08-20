terraform {
  required_version = ">= 1.5"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

# Backend local: el archivo de estado queda en esta misma carpeta
# (terraform.tfstate). En un caso real sería un backend remoto (S3 + DynamoDB,
# como muestra el post), pero el mecanismo de "state = fuente de verdad" es
# el mismo.
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}

# Este recurso representa, de forma declarativa, un "servidor web": en vez de
# describir los pasos para crearlo (enfoque imperativo), describimos el
# estado final deseado y dejamos que Terraform calcule el plan de ejecución.
# Usamos el provider "local" (built-in, sin cuenta cloud) para que el ejemplo
# corra en cualquier máquina sin credenciales: escribe un archivo JSON que
# representa la infraestructura declarada.
resource "local_file" "web_server" {
  filename = "${path.module}/output/web-server.json"

  content = jsonencode({
    resource_type = "web_server"
    environment   = var.environment
    instance_type = var.instance_type
    managed_by    = "terraform"
  })
}
