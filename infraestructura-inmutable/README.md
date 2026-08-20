# Infraestructura Inmutable: golden image + blue-green local con Docker

Ejemplo del post [Infraestructura Inmutable: Guía Definitiva para DevOps 2025](https://www.devopsfreelance.pro/blog/posts/infraestructura-inmutable/).

## Qué demuestra

El post explica infraestructura inmutable usando Packer (golden images / AMI),
Terraform (Launch Template + Auto Scaling Group) y despliegues blue-green en
AWS. Ese flujo no se puede correr gratis en una laptop, así que este ejemplo
traduce el mismo patrón a herramientas 100% locales:

- **Golden image = imagen Docker inmutable**: el `Dockerfile` hornea la
  versión de la app (`APP_VERSION`) y su color de despliegue
  (`DEPLOYMENT_COLOR`) en build time, igual que Packer hornea la AMI. Una vez
  construida, la imagen nunca se modifica in-place.
- **Blue-Green deployment**: `deploy-blue-green.sh` construye una nueva
  golden image (Green), la levanta al lado de la que está en producción
  (Blue), le pasa un health check, mueve el tráfico de un balanceador (nginx)
  de Blue a Green, y recién ahí apaga Blue. Es el mismo flujo del bloque
  `instance_refresh` de Terraform del post, pero con contenedores en vez de
  instancias EC2.
- **Rollback trivial**: si algo falla, se revierte el tráfico a Blue en vez
  de "arreglar" Green. El script lo deja documentado en su output final.
- **Estado externalizado**: la app no persiste nada en disco local; solo
  responde con su propia versión y hostname, ilustrando por qué los
  servidores inmutables deben ser stateless.

Fuera de alcance de este ejemplo (para no sobrecargarlo): Packer/AMI real,
Terraform/ASG real, CI/CD del pipeline. El README de esos puntos queda
documentado en el post; acá se demuestra el concepto central (golden
image + reemplazo sin downtime) de forma ejecutable.

## Requisitos

- Docker y Docker Compose v2 (`docker compose version` debe funcionar)
- `curl` y `python3` (para verificar la salida; python3 solo se usa en tu
  máquina para el `json.tool`, no es requisito estricto)

No se requiere cuenta de AWS ni ningún servicio pago.

## Cómo correrlo

```bash
cd infraestructura-inmutable

# 1. Construir y levantar la golden image "Blue" (v1) detrás de nginx
docker compose up -d --build blue nginx

# 2. Verificar que Blue está sirviendo trafico
curl -s http://localhost:8080 | python3 -m json.tool
# {
#     "app_version": "v1",
#     "deployment_color": "blue",
#     "hostname": "..."
# }

# 3. Ejecutar el despliegue blue-green: construye Green (v2), la prueba,
#    mueve el trafico y apaga Blue
chmod +x deploy-blue-green.sh
./deploy-blue-green.sh

# 4. Verificar que ahora responde Green (v2), sin downtime perceptible
curl -s http://localhost:8080 | python3 -m json.tool
# {
#     "app_version": "v2",
#     "deployment_color": "green",
#     "hostname": "..."
# }

# 5. Limpiar todo
docker compose --profile green down
rm -f nginx.conf.bak
```

## Salida esperada

- Antes del deploy: `deployment_color: "blue"`, `app_version: "v1"`.
- El script `deploy-blue-green.sh` imprime 5 pasos (build, deploy, health
  check, switch de tráfico, apagado de Blue) y termina con instrucciones de
  rollback.
- Después del deploy: `deployment_color: "green"`, `app_version: "v2"`, sin
  haber tocado el contenedor Blue in-place (Blue simplemente queda detenido,
  listo para destruirse o para un rollback).

## Rollback (opcional)

El propio script deja el comando impreso al final. En resumen: restaura
`nginx.conf` desde el backup, vuelve a arrancar Blue, recarga nginx y apaga
Green. Ningún paso requiere editar un servidor corriendo, tal como describe
el post.
