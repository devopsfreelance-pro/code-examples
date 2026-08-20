# main.tf
# Provisiona una VM KVM como codigo usando el provider de libvirt para Terraform.
# Requiere un host Linux con KVM/libvirt instalado (ver README.md del ejemplo).

terraform {
  required_version = ">= 1.5"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.7.6"
    }
  }
}

variable "libvirt_uri" {
  description = "URI de conexion al daemon libvirt"
  type        = string
  default     = "qemu:///system"
}

variable "vm_name" {
  description = "Nombre de la VM a crear"
  type        = string
  default     = "demo-web-server"
}

variable "vm_memory_mb" {
  description = "Memoria RAM de la VM en MB"
  type        = number
  default     = 1024
}

variable "vm_vcpu" {
  description = "Cantidad de vCPUs de la VM"
  type        = number
  default     = 1
}

provider "libvirt" {
  uri = var.libvirt_uri
}

# Imagen base de Ubuntu cloud, se descarga una sola vez y se reutiliza
# como capa base (copy-on-write) para cada VM.
resource "libvirt_volume" "ubuntu_base" {
  name   = "ubuntu-base.qcow2"
  pool   = "default"
  source = "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
  format = "qcow2"
}

# Disco propio de la VM, basado en la imagen base (copy-on-write)
resource "libvirt_volume" "vm_disk" {
  name           = "${var.vm_name}.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.ubuntu_base.id
  size           = 10 * 1024 * 1024 * 1024 # 10GB
}

# cloud-init minimo: crea usuario y habilita login por password para la demo
resource "libvirt_cloudinit_disk" "cloudinit" {
  name = "${var.vm_name}-cloudinit.iso"
  pool = "default"
  user_data = <<-EOT
    #cloud-config
    users:
      - name: devops
        sudo: ALL=(ALL) NOPASSWD:ALL
        shell: /bin/bash
        lock_passwd: false
        plain_text_passwd: 'devops'
    package_update: true
    packages:
      - qemu-guest-agent
  EOT
}

resource "libvirt_domain" "vm" {
  name   = var.vm_name
  memory = var.vm_memory_mb
  vcpu   = var.vm_vcpu

  cloudinit = libvirt_cloudinit_disk.cloudinit.id

  disk {
    volume_id = libvirt_volume.vm_disk.id
  }

  network_interface {
    network_name   = "default"
    wait_for_lease = true
  }

  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }

  graphics {
    type        = "spice"
    listen_type = "address"
  }
}

output "vm_name" {
  value = libvirt_domain.vm.name
}

output "vm_ip" {
  value = try(libvirt_domain.vm.network_interface[0].addresses[0], "pendiente (esperar lease DHCP)")
}
