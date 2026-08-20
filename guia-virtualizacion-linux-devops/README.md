# Ejemplo: Virtualización Linux para DevOps (KVM, LXD, Terraform)

Post: [Guía Definitiva de Virtualización Linux: Estrategias DevOps](https://www.devopsfreelance.pro/blog/posts/guia-virtualizacion-linux-devops/)

## Qué demuestra este ejemplo

Tres piezas mínimas que cubren el hilo central del post: diagnóstico de
soporte de virtualización de hardware, comparación práctica de niveles de
aislamiento (LXC/LXD vs Docker) y automatización de una VM KVM como código
con Terraform (provider `libvirt`).

- `scripts/check-virtualization.sh`: valida que el host soporta KVM
  (extensiones vmx/svm, módulo del kernel, herramientas instaladas) y resume
  las diferencias de overhead/aislamiento entre KVM, LXC/LXD y Docker/Podman.
- `scripts/lxd-vs-docker-demo.sh`: levanta un contenedor LXD (sistema
  completo con systemd) y un contenedor Docker (proceso único) para que se
  vea la diferencia de aislamiento en la práctica.
- `terraform/main.tf`: define una VM KVM completa (disco base + cloud-init +
  red) como código, igual que en la sección "Automatización con Terraform"
  del post.

## Requisitos

- Linux con soporte de virtualización de hardware habilitado en BIOS/UEFI
  (Intel VT-x o AMD-V). Verificable con `egrep -c '(vmx|svm)' /proc/cpuinfo`.
- Para el diagnóstico (`check-virtualization.sh`): sin dependencias
  obligatorias, corre en cualquier Linux. Para la sección `kvm-ok` (opcional):
  `sudo apt install cpu-checker` (Debian/Ubuntu).
- Para la demo de aislamiento (`lxd-vs-docker-demo.sh`):
  - LXD: `sudo snap install lxd && sudo lxd init --auto`
  - Docker: `curl -fsSL https://get.docker.com | sh`
  (el script detecta cuál está disponible y corre solo esa parte si falta la otra)
- Para el ejemplo de Terraform:
  - `qemu-kvm`, `libvirt-daemon-system`, `libvirt-clients` instalados y
    `libvirtd` activo (ver comandos de instalación en el post).
  - Tu usuario en los grupos `libvirt` y `kvm`.
  - [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.

No se necesita ninguna cuenta ni credencial paga: todo corre localmente
contra el daemon `libvirtd` del propio host (`qemu:///system`).

> **Nota sobre CI/runners**: el ejemplo de Terraform (`terraform/`) no puede
> ejecutarse en un runner de CI estandar (GitHub Actions, etc.): necesita un
> daemon `libvirtd` corriendo localmente con acceso a `/dev/kvm`
> (virtualizacion de hardware), algo que estos runners no exponen. `tofu
> plan`/`terraform plan` solo funcionan en un host real con KVM/libvirt
> instalado y configurado como se describe arriba.

## Pasos para correrlo

### 1. Diagnóstico de virtualización

```bash
cd scripts
chmod +x check-virtualization.sh
./check-virtualization.sh
```

Salida esperada (resumida, varía según el host):

```
== Diagnostico de virtualizacion Linux ==

-- 1. Extensiones de CPU (vmx/svm) --
OK: el CPU expone 8 extensiones de virtualizacion (vmx/svm)

-- 2. Modulo KVM en el kernel --
OK: modulo kvm cargado
  - kvm_intel
  - kvm

-- 3. kvm-ok (si esta instalado) --
INFO/KVM: /dev/kvm exists
KVM acceleration can be used

-- 4. Herramientas instaladas --
OK: virsh disponible (/usr/bin/virsh)
no instalado: lxc
OK: docker disponible (/usr/bin/docker)
...

Diagnostico completo.
```

### 2. Comparar aislamiento LXD vs Docker

```bash
cd scripts
chmod +x lxd-vs-docker-demo.sh
./lxd-vs-docker-demo.sh
```

Salida esperada: en la parte de LXD vas a ver una lista de procesos con
`systemd` como PID 1 (sistema completo); en la parte de Docker vas a ver un
único proceso (`nginx`), sin `systemd` ni init propio. Eso ilustra la
diferencia de aislamiento "medio" (LXD) vs "orientado a la aplicación"
(Docker) que describe el post.

### 3. Provisionar una VM KVM con Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Salida esperada al final del `apply`:

```
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

vm_ip = "192.168.122.XXX"
vm_name = "demo-web-server"
```

Verificar la VM creada con las herramientas del post:

```bash
virsh list --all
virsh dominfo demo-web-server
```

Login por consola serie (usuario `devops`, password `devops`, definidos en
el cloud-init del `main.tf`):

```bash
virsh console demo-web-server
```

Para destruir la VM y liberar los recursos:

```bash
terraform destroy
```

## Notas

- El ejemplo de Terraform descarga la imagen cloud de Ubuntu 22.04 (~600MB)
  la primera vez que corre `apply`; quedará cacheada en el pool `default` de
  libvirt para corridas siguientes.
- La contraseña `devops` del cloud-init es solo para esta demo local. No usar
  en un entorno real: reemplazar por una clave SSH (`ssh_authorized_keys` en
  el `user_data` de `libvirt_cloudinit_disk`).
