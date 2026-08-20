#!/usr/bin/env bash
# Simula un pico de CPU y muestra como responderia el Auto Scaling Group.
# Contra LocalStack Community las alarm_actions no disparan el scaling
# automaticamente (eso requiere LocalStack Pro), asi que este script hace
# explicito el mismo flujo que ejecutaria AWS real: cambia el estado de la
# alarma a ALARM y despues ajusta la capacidad deseada del ASG, para que
# puedas ver el efecto de "escalar por CPU alta" sin cuenta de AWS.
set -euo pipefail

ENDPOINT="http://localhost:4566"
REGION="us-east-1"
ASG_NAME="escalabilidad-aws-asg"
ALARM_NAME="escalabilidad-aws-cpu-high"

AWS="aws --endpoint-url=${ENDPOINT} --region=${REGION}"

echo "== Estado inicial del Auto Scaling Group =="
$AWS autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "${ASG_NAME}" \
  --query "AutoScalingGroups[0].{Min:MinSize,Desired:DesiredCapacity,Max:MaxSize}" \
  --output table

echo
echo "== Disparando la alarma de CPU alta (simula CPU > 70%) =="
$AWS cloudwatch set-alarm-state \
  --alarm-name "${ALARM_NAME}" \
  --state-value ALARM \
  --state-reason "Simulacion de pico de trafico para el demo del post"

echo
echo "== Escalando el ASG como respuesta al pico (scale-out manual, equivalente al efecto de la policy) =="
$AWS autoscaling set-desired-capacity \
  --auto-scaling-group-name "${ASG_NAME}" \
  --desired-capacity 6 \
  --honor-cooldown

echo
echo "== Estado del Auto Scaling Group tras el scale-out =="
$AWS autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "${ASG_NAME}" \
  --query "AutoScalingGroups[0].{Min:MinSize,Desired:DesiredCapacity,Max:MaxSize}" \
  --output table

echo
echo "== Volviendo la alarma a OK (simula que la CPU bajo) =="
$AWS cloudwatch set-alarm-state \
  --alarm-name "${ALARM_NAME}" \
  --state-value OK \
  --state-reason "Simulacion: CPU vuelta a valores normales"
