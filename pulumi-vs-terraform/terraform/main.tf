terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

variable "container_name" {
  description = "Nombre del contenedor"
  default     = "web-server-terraform"
}

variable "external_port" {
  description = "Puerto en el host mapeado al puerto 80 del contenedor"
  default     = 8081
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "web_server" {
  name  = var.container_name
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = var.external_port
  }
}

output "url" {
  value = "http://localhost:${var.external_port}"
}

output "container_id" {
  value = docker_container.web_server.id
}
