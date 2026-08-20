# Gestión de configuración con Ansible - Ejemplo ejecutable

Post: [Guía Completa de Gestión de configuración con Ansible](https://www.devopsfreelance.pro/blog/posts/gestion-configuracion-con-ansible/)

## Qué demuestra este ejemplo

Un playbook mínimo de Ansible que aplica el concepto central del post: **configuración
declarativa e idempotente** contra un inventario con varios hosts y variables por host.

- Un `inventory.ini` estático con dos hosts (`web01`, `web02`) y una variable por host
  (`environment_name`) más una variable de grupo (`http_port`), igual que el ejemplo
  de inventarios del post.
- Un playbook (`site.yml`) que instala Nginx, despliega una página desde una plantilla
  Jinja2 (`templates/index.html.j2`) personalizada por host, y arranca el servicio.
- Los hosts son contenedores Docker (no hace falta AWS, SSH ni claves): Ansible se
  conecta con el plugin `docker`, sin agentes ni configuración extra.
- Al correr el playbook una segunda vez sin cambios, Ansible reporta `changed=0`
  en las tareas de instalación y despliegue: eso es idempotencia en acción.

No se cubre todo el post (roles, Vault, CI/CD, inventarios dinámicos de AWS): es
un recorte mínimo y ejecutable del núcleo del tema.

## Requisitos

- Docker y Docker Compose
- Python 3 y `pip` en tu máquina (para instalar Ansible)
- `ansible-core` (se instala en el paso 2)

## Pasos

### 1. Levantar los hosts (contenedores Docker)

```bash
cd gestion-configuracion-con-ansible
docker compose up -d
```

Esto crea dos contenedores Ubuntu 22.04 (`web01`, `web02`) que actúan como los
hosts gestionados, con los puertos 8080 y 8081 mapeados al 80 de cada uno.

### 2. Instalar Ansible

```bash
pip install --user ansible-core
```

### 3. Ejecutar el playbook

```bash
ansible-playbook -i inventory.ini site.yml
```

Salida esperada (resumen): las tareas de instalación de Python, Nginx, despliegue
de la plantilla e inicio del servicio en estado `changed` para ambos hosts:

```
PLAY RECAP *********************************************************
web01  : ok=5    changed=3    unreachable=0    failed=0
web02  : ok=5    changed=3    unreachable=0    failed=0
```

### 4. Verificar el resultado

```bash
curl http://localhost:8080   # debería mostrar "Entorno: blue"
curl http://localhost:8081   # debería mostrar "Entorno: green"
```

### 5. Comprobar la idempotencia

Corré el mismo playbook otra vez sin tocar nada:

```bash
ansible-playbook -i inventory.ini site.yml
```

Salida esperada: `changed=0` en la instalación de Nginx y el despliegue de la
plantilla (ya están en el estado deseado), y `ok` en el arranque del servicio
porque el archivo `/run/nginx.pid` ya existe:

```
PLAY RECAP *********************************************************
web01  : ok=5    changed=0    unreachable=0    failed=0
web02  : ok=5    changed=0    unreachable=0    failed=0
```

Este es el punto central del post: ejecutar el mismo playbook múltiples veces
produce siempre el mismo resultado final, sin efectos colaterales.

### 6. Limpiar

```bash
docker compose down
```

## Archivos

- `docker-compose.yml` - Levanta dos contenedores Ubuntu que Ansible gestiona como hosts.
- `inventory.ini` - Inventario estático con grupo `webservers`, variables por host y por grupo.
- `site.yml` - Playbook: instala Nginx, despliega configuración vía plantilla, arranca el servicio de forma idempotente.
- `templates/index.html.j2` - Plantilla Jinja2 personalizada según las variables de cada host.

No hay secretos ni credenciales en este ejemplo.
