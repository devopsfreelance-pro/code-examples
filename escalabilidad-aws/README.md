# Escalabilidad en AWS: Auto Scaling Group + alarma de CloudWatch

Post: https://www.devopsfreelance.pro/blog/posts/escalabilidad-aws/

## Qué demuestra este ejemplo

El post explica el mecanismo central de la escalabilidad horizontal en AWS:
un Auto Scaling Group que crece o se reduce automáticamente cuando una
alarma de CloudWatch detecta CPU alta, usando una política de escalado por
target tracking. Este ejemplo reproduce exactamente esos componentes con
Terraform:

- Un `aws_launch_template` (cómo se lanza cada instancia).
- Un `aws_autoscaling_group` con `min_size=2`, `max_size=10`,
  `desired_capacity=2`, igual que el ejemplo del post.
- Una `aws_autoscaling_policy` de tipo `TargetTrackingScaling` sobre
  `ASGAverageCPUUtilization` al 70%, igual al `config.json` del post.
- Una `aws_cloudwatch_metric_alarm` que dispara la política cuando la CPU
  supera 70% durante 2 minutos, igual a la alarma CloudFormation del post.

Corre 100% local contra [LocalStack](https://www.localstack.cloud/)
(servicios `ec2`, `autoscaling`, `cloudwatch`, `elbv2`, `iam`, `sts`), sin
cuenta de AWS ni costo. Un script (`scale-test.sh`) simula un pico de
tráfico disparando la alarma y ajustando la capacidad del ASG, para que
veas el efecto de "escalar por CPU alta" sin esperar carga real.

> Nota: LocalStack Community no ejecuta automáticamente las
> `alarm_actions` de CloudWatch (eso requiere LocalStack Pro). El script
> `scale-test.sh` hace explícito el mismo flujo que dispararía AWS real:
> pone la alarma en estado `ALARM` y después ajusta `desired_capacity`,
> para que el efecto de la política sea visible en minutos sin cuenta paga.

## Requisitos

- Docker + Docker Compose
- Terraform >= 1.0 (`terraform version`)
- AWS CLI (`aws --version`)
- curl (para chequear que LocalStack levantó)

## Pasos para correrlo

1. Levantar LocalStack:

   ```bash
   docker compose up -d
   ```

2. Esperar a que los servicios necesarios estén disponibles:

   ```bash
   until curl -s http://localhost:4566/_localstack/health | grep -q '"autoscaling": "available"'; do
     sleep 2
   done
   ```

3. Inicializar y aplicar Terraform:

   ```bash
   terraform init
   terraform apply -auto-approve
   ```

   Salida esperada (resumen):

   ```
   Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

   Outputs:

   autoscaling_group_name = "escalabilidad-aws-asg"
   cloudwatch_alarm_name = "escalabilidad-aws-cpu-high"
   launch_template_id = "lt-xxxxxxxxxxxxxxxxx"
   ```

4. Verificar el Auto Scaling Group creado:

   ```bash
   aws --endpoint-url=http://localhost:4566 --region=us-east-1 \
     autoscaling describe-auto-scaling-groups \
     --auto-scaling-group-names escalabilidad-aws-asg \
     --query "AutoScalingGroups[0].{Min:MinSize,Desired:DesiredCapacity,Max:MaxSize}" \
     --output table
   ```

   Salida esperada:

   ```
   ----------------------
   |DescribeAutoScaling..|
   +------+---------+----+
   | Desired| Max | Min  |
   +------+---------+----+
   |  2     | 10  | 2    |
   +------+---------+----+
   ```

5. Simular un pico de CPU y observar el scale-out:

   ```bash
   chmod +x scale-test.sh
   ./scale-test.sh
   ```

   Salida esperada (resumen): el bloque "Estado inicial" muestra
   `Desired: 2`, y el bloque "tras el scale-out" muestra `Desired: 6`,
   confirmando que el ASG respondió al pico simulado dentro del rango
   `min=2` / `max=10` definido en `main.tf`.

6. Limpiar todo al terminar:

   ```bash
   terraform destroy -auto-approve
   docker compose down -v
   ```

## Archivos

- `docker-compose.yml`: levanta LocalStack con los servicios necesarios.
- `main.tf`: VPC mínima, Launch Template, Auto Scaling Group, política de
  target tracking y alarma de CloudWatch.
- `outputs.tf`: nombres/IDs de los recursos creados, para copiar y pegar en
  los comandos de verificación.
- `scale-test.sh`: dispara la alarma y ajusta la capacidad del ASG para
  simular el efecto de un pico de tráfico.
