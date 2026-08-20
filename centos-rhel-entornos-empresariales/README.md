# Demo: gestión de paquetes RPM y repositorio interno (estilo CentOS/RHEL)

Post: [CentOS Production: Guía para Entornos Empresariales 2026](https://www.devopsfreelance.pro/blog/posts/centos-rhel-entornos-empresariales/)

## Qué demuestra

El post explica cómo se administran paquetes con RPM/dnf y cómo las empresas
mantienen repositorios internos propios para controlar qué versiones de
software llegan a producción (compliance, auditorías, rollbacks).

Este ejemplo reproduce ese flujo completo en un contenedor local, usando
Rocky Linux 9 (clon binario-compatible de RHEL, sin necesidad de suscripción
de Red Hat):

1. Verificación de integridad de paquetes instalados (`rpm -Va`).
2. Consulta de metadatos de un paquete (`rpm -qi`).
3. Listado de archivos que instala un paquete (`rpm -ql`).
4. Identificación del paquete dueño de un archivo (`rpm -qf`).
5. Creación de un repositorio interno con `createrepo_c`.
6. Configuración de ese repo en `/etc/yum.repos.d/internal.repo`, igual que
   en el post.
7. Consulta del repositorio interno recién creado con `dnf`.

## Requisitos

- Docker y Docker Compose (`docker compose version`).
- Conexión a internet solo durante el build de la imagen (para instalar
  `createrepo_c`, `httpd`, `nginx` vía dnf desde los repos de Rocky Linux).

No se usa RHEL real ni `subscription-manager`: Rocky Linux ofrece los mismos
comandos y formato de paquetes sin costo, ideal para practicar localmente lo
que en la empresa se haría contra RHEL con suscripción.

## Cómo correrlo

```bash
cd centos-rhel-entornos-empresariales
docker compose up --build
```

Esto construye la imagen (instala `createrepo_c`, `httpd`, `nginx`) y ejecuta
`rpm-repo-demo.sh`, que corre los 7 pasos descritos arriba en orden.

Para limpiar el contenedor al terminar:

```bash
docker compose down
```

## Salida esperada

Vas a ver en la terminal, en este orden:

```
=== 1) Verificar la integridad de paquetes instalados ===
...
=== 2) Consultar información detallada de un paquete (httpd) ===
Name        : httpd
Version     : 2.4...
...
=== 3) Listar archivos instalados por un paquete (nginx) ===
/etc/nginx
/etc/nginx/nginx.conf
...
=== 4) Identificar qué paquete provee un archivo del sistema ===
python3-3...

=== 5) Crear un repositorio interno con los RPM ya cacheados por dnf ===
...
Directory walk started
Directory walk done - X packages
...
Repo saved

=== 6) Configurar el repositorio interno (equivalente a /etc/yum.repos.d/internal.repo) ===

=== 7) Consultar el repositorio interno recién creado ===
repo id           repo name
internal-base     Internal Base Repository
...

=== Demo completa: paquetes instalados, metadatos consultados y repo interno operativo. ===
```

Los números de versión exactos dependen de los paquetes disponibles en el
mirror de Rocky Linux al momento de correr el demo, pero la secuencia de
pasos y el resultado (repo interno propio funcionando) siempre es el mismo.
