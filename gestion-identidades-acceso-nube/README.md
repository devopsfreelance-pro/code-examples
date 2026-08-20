# Gestión de identidades y acceso en la nube: motor de evaluación de políticas IAM

Post relacionado: [Guía Completa de Gestión de identidades y acceso en la nube](https://www.devopsfreelance.pro/blog/posts/gestion-identidades-acceso-nube/)

## Qué demuestra este ejemplo

El post explica el concepto central de la autorización en IAM cloud: dado un
usuario/servicio ya autenticado, el sistema decide si una acción sobre un
recurso se permite o se deniega evaluando políticas (JSON, como el ejemplo de
AWS IAM del post) que combinan RBAC/ABAC y condiciones de contexto (IP de
origen, si la conexión usa TLS, etc.).

Este ejemplo reimplementa en Python puro el algoritmo real que usa AWS IAM
(y que Azure/GCP aplican con otros nombres) para tomar esa decisión:

1. Un **Deny explícito** en cualquier política gana siempre, sin importar
   cuántos Allow existan (guardrail de seguridad).
2. Si no hay Deny, se necesita al menos un **Allow** que matchee acción +
   recurso + condiciones.
3. Si ninguna política matchea, el resultado es **Deny implícito**
   (least privilege por defecto).

`policy_evaluator.py` carga las políticas de `policies/`, corre una batería
de solicitudes de `requests.json` contra ellas y muestra la decisión con su
motivo, tal como haría `aws iam simulate-custom-policy` pero sin necesitar
una cuenta de AWS.

Los cinco casos de prueba cubren:

- Acceso permitido a S3 cumpliendo las condiciones de IP y TLS de la
  política del post.
- Acceso denegado por recurso fuera del alcance de la política (least
  privilege).
- Acceso denegado por incumplir una condición (sin TLS).
- Acceso de administrador de IAM permitido desde la red corporativa
  confiable.
- El mismo acceso de administrador denegado desde fuera de esa red: el
  guardrail de "Deny explícito" gana por encima del Allow de la política de
  administrador, ilustrando por qué el orden de evaluación de AWS IAM importa.

## Requisitos

- Python 3 (sin dependencias externas, solo librería estándar)

## Cómo correrlo

```bash
python3 policy_evaluator.py
```

## Salida esperada

```
[OK ] App autorizada lee un objeto del bucket de datos, desde la IP permitida y por HTTPS
       accion=s3:GetObject recurso=arn:aws:s3:::mi-bucket-datos/reporte.csv
       decision=Allow (esperado=Allow)
       motivo: Allow en statement 'AllowReadDataBucket' de policy 'app-policy'

[OK ] Misma app intenta acceder a un bucket que NO esta en la policy (fuera de alcance)
       accion=s3:GetObject recurso=arn:aws:s3:::otro-bucket-cualquiera/archivo.txt
       decision=Deny (esperado=Deny)
       motivo: Deny implicito: ningun Allow matcheo accion+recurso+condiciones

[OK ] Misma app intenta el mismo GetObject pero por HTTP en texto plano (sin TLS)
       accion=s3:GetObject recurso=arn:aws:s3:::mi-bucket-datos/reporte.csv
       decision=Deny (esperado=Deny)
       motivo: Deny implicito: ningun Allow matcheo accion+recurso+condiciones

[OK ] Administrador de IAM operando desde la red corporativa confiable (10.0.0.0/8)
       accion=iam:CreateUser recurso=arn:aws:iam::123456789012:user/nuevo-empleado
       decision=Allow (esperado=Allow)
       motivo: Allow en statement 'AllowIamAdminFromTrustedNetwork' de policy 'admin-policy'

[OK ] Alguien con la policy de administrador de IAM intenta usarla desde fuera de la red confiable: el guardrail de deny explicito gana
       accion=iam:CreateUser recurso=arn:aws:iam::123456789012:user/nuevo-empleado
       decision=Deny (esperado=Deny)
       motivo: Deny explicito en statement 'DenyIamChangesFromOutsideOffice' de policy 'guardrail-deny-privilege-escalation'
```

El script termina con código de salida `0` si todas las decisiones coinciden
con lo esperado (`1` si alguna falla), útil para engancharlo a un pipeline de
"Policy as Code" como el `GitHub Actions` del post.

## Estructura

```
gestion-identidades-acceso-nube/
├── policy_evaluator.py                          # Motor de evaluación (Allow/Deny/condiciones)
├── requests.json                                # Casos de prueba (solicitudes de acceso)
└── policies/
    ├── app-policy.json                          # Allow S3 con condiciones IP + TLS (tomado del post)
    ├── admin-policy.json                        # Allow amplio de IAM desde red confiable
    └── guardrail-deny-privilege-escalation.json # Deny explícito fuera de la red confiable
```

## Ir más allá

Para probar los mismos conceptos contra AWS real (sin gastar), se puede
adaptar `policies/app-policy.json` a `aws iam simulate-custom-policy
--policy-input-list file://policies/app-policy.json --action-names
s3:GetObject --resource-arns arn:aws:s3:::mi-bucket-datos/reporte.csv`, tal
como muestra el paso "Validate IAM policies" del pipeline de GitHub Actions
del post.
