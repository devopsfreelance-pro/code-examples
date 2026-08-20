# Estrategias híbridas y multi-cloud: demo de IaC agnóstica al proveedor

Post: [Guía Completa de Estrategias híbridas y multi-cloud](https://www.devopsfreelance.pro/blog/posts/estrategias-hibridas-multi-cloud/)

## Qué demuestra este ejemplo

El post explica que uno de los pilares técnicos de una estrategia híbrida/multi-cloud
es el **aprovisionamiento declarativo y agnóstico al proveedor mediante Infrastructure
as Code** (Terraform, Pulumi, Crossplane), combinando recursos on-premise con recursos
en distintos proveedores cloud desde el mismo flujo.

Este ejemplo levanta, con un solo `terraform apply`, dos "entornos" en paralelo:

- **Entorno cloud**: un bucket S3 provisionado contra [LocalStack](https://www.localstack.cloud/)
  (emula la API de AWS localmente, sin cuenta ni costo real).
- **Entorno on-premise**: un contenedor Docker con Nginx, que simula un servicio corriendo
  en infraestructura propia (datacenter/local).

Ambos recursos se definen con el mismo lenguaje (HCL) y el mismo comando de despliegue,
ilustrando la capa de abstracción que permite gestionar infraestructura híbrida de forma
unificada, tal como describe el post.

## Requisitos

- Docker y Docker Compose
- Terraform >= 1.5
- (Opcional) AWS CLI, solo para el script de verificación

No se necesita ninguna cuenta cloud real ni credenciales: todo corre en local.

## Pasos para ejecutarlo

1. Levantar LocalStack (emula AWS S3):

   ```bash
   docker compose up -d
   ```

2. Esperar unos segundos a que LocalStack esté listo y verificar:

   ```bash
   curl -s http://localhost:4566/_localstack/health
   ```

3. Inicializar y aplicar Terraform (provisiona el bucket "cloud" y el contenedor "on-premise"):

   ```bash
   terraform init
   terraform apply -auto-approve
   ```

4. Verificar que ambos entornos quedaron operativos:

   ```bash
   ./verificar.sh
   ```

5. Ver el servicio on-premise en el navegador o con curl:

   ```bash
   curl -s http://localhost:8080 | head -n 5
   ```

## Salida esperada

Al terminar `terraform apply`, Terraform muestra las salidas:

```
Outputs:

cloud_bucket_name = "hybrid-demo-cloud-artifacts"
onprem_container_name = "hybrid-demo-onprem-web"
onprem_url = "http://localhost:8080"
```

`./verificar.sh` debe imprimir:

```
== Verificando entorno cloud (LocalStack / S3) ==
OK: bucket cloud encontrado

== Verificando entorno on-premise (contenedor Docker) ==
OK: contenedor on-premise corriendo
OK: servicio on-premise responde en http://localhost:8080
```

Y `curl http://localhost:8080` devuelve la página de bienvenida de Nginx.

## Limpieza

```bash
terraform destroy -auto-approve
docker compose down -v
```

## Notas

- En un escenario real, el provider `aws` apuntaría a la API real de AWS (sin el bloque
  `endpoints`) y el "on-premise" podría ser un provider de vSphere, un cluster Kubernetes
  propio, o cualquier proveedor Terraform que exponga tu infraestructura local.
- Las credenciales `test`/`test` del provider `aws` son las que exige LocalStack por
  convención y no son secretos reales.
