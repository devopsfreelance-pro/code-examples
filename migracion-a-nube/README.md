# Migración a la Nube: Estrategias 6R y Guía de Implementación

Post: https://www.devopsfreelance.pro/blog/posts/migracion-a-nube/

## Qué demuestra este ejemplo

El post describe dos cosas concretas que se pueden ejecutar: el marco de las
**6 R** para clasificar aplicaciones (Rehost, Replatform, Refactor,
Repurchase, Retire, Retain) y la preparación de la infraestructura cloud
(VPC con subnets) donde aterrizan las apps ya migradas. Este ejemplo cubre
ambas piezas a escala mínima:

1. **`classify_apps.py`** toma un inventario de 6 aplicaciones on-premise
   (criticidad, complejidad técnica, antigüedad) y aplica reglas simples
   inspiradas en el marco de las 6 R para asignarle una estrategia a cada
   una. Agrupa el resultado en oleadas de migración (retire/retain primero,
   rehost después, replatform/repurchase luego, refactor al final) y
   registra cada app como una instancia EC2 tagueada en LocalStack —
   reemplaza a AWS Application Discovery Service (servicio de pago, no
   disponible en LocalStack Community) manteniendo la misma idea de
   inventario con metadata consultable.
2. **`main.tf`** crea el landing zone destino: una VPC con subnets privadas
   (una por availability zone), siguiendo el ejemplo conceptual de Terraform
   del post, pero completo y aplicable (route table incluida).

No incluye AWS DMS (replicación de bases de datos) porque ese servicio no
está disponible en LocalStack Community; el post ya cubre esa parte con
código conceptual.

Corre 100% local contra [LocalStack](https://www.localstack.cloud/)
(servicios `ec2`, `iam`, `sts`), sin cuenta de AWS ni costo.

## Requisitos

- Docker + Docker Compose
- Terraform >= 1.0 (`terraform version`)
- Python 3.9+ con `pip`
- curl (para chequear que LocalStack levantó)

## Pasos para correrlo

1. Levantar LocalStack:

   ```bash
   docker compose up -d
   ```

2. Esperar a que el servicio EC2 esté disponible:

   ```bash
   until curl -s http://localhost:4566/_localstack/health | grep -q '"ec2": "available"'; do
     sleep 2
   done
   ```

3. Instalar las dependencias de Python y correr la clasificación 6R:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python3 classify_apps.py
   ```

4. Inicializar y aplicar Terraform para crear el landing zone destino:

   ```bash
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   terraform output
   ```

5. (Opcional) Confirmar que el inventario quedó tagueado en LocalStack:

   ```bash
   aws --endpoint-url=http://localhost:4566 ec2 describe-instances \
     --query 'Reservations[].Instances[].Tags' --output table
   ```

   (Requiere AWS CLI instalado; si no lo tenés, el reporte de
   `classify_apps.py` en el paso 3 ya muestra la misma información.)

6. Limpiar todo al terminar:

   ```bash
   terraform destroy -auto-approve
   docker compose down -v
   deactivate
   ```

## Salida esperada

Del paso 3 (`classify_apps.py`):

```
Plan de migracion por oleadas (6R)
========================================

Oleada 1:
  - reporting-cronjobs             strategy=retire     criticality=low    age=10y
  - old-intranet-portal            strategy=retain     criticality=low    age=12y

Oleada 2:
  - web-frontend-legacy            strategy=rehost     criticality=high   age=2y

Oleada 3:
  - internal-crm-custom            strategy=repurchase criticality=medium age=8y
  - auth-service                   strategy=replatform criticality=high   age=3y

Oleada 4:
  - billing-mainframe-batch        strategy=refactor   criticality=high   age=15y
```

Del paso 4 (`terraform apply`):

```
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

private_subnet_ids = [
  "subnet-xxxxxxxx",
  "subnet-xxxxxxxx",
  "subnet-xxxxxxxx",
]
subnet_count = 3
vpc_id = "vpc-xxxxxxxx"
```

Los IDs son generados por LocalStack en cada corrida, van a variar.

## Notas

- El provider AWS y el cliente boto3 apuntan a `http://localhost:4566`
  (endpoint único de LocalStack) con credenciales dummy (`test`/`test`); no
  se necesita cuenta real de AWS.
- Las reglas de clasificación en `classify_apps.py` son una simplificación
  didáctica del marco de las 6 R, no un motor de decisión real: en un
  proyecto real la clasificación sale de la evaluación de portafolio que
  describe el post (dependencias, costos, criticidad de negocio real).
- Si corrés `classify_apps.py` sin haber levantado `docker compose up -d`,
  el script avisa por stderr y de todas formas imprime el reporte de
  oleadas (la parte de registro en LocalStack es la única que falla).
