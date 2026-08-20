# IAM Cloud: simulador de evaluacion de politicas

Ejemplo de codigo para el post [IAM Cloud: Gestion de Identidades y Acceso en DevOps 2025](https://www.devopsfreelance.pro/blog/posts/iam-cloud-gestion-identidades-acceso/).

## Que demuestra

El post explica que una configuracion IAM deficiente es la causa principal
de brechas de seguridad en la nube, y que el motor de evaluacion de AWS
sigue reglas precisas: **deny explicito siempre gana**, **sin un allow
que matchee el resultado es deny implicito**, y un **permission boundary**
solo puede acotar permisos, nunca otorgarlos.

Este ejemplo implementa un mini motor de evaluacion de politicas IAM en
Python puro (`policy_simulator.py`) y lo corre contra las tres politicas
JSON reales usadas en el post:

- `policies/least-privilege-s3.json`: acceso de solo lectura a un bucket S3
  condicionado a la IP de origen (seccion "Anatomia de una Politica IAM").
- `policies/permission-boundary.json` + `policies/broad-identity-policy.json`:
  como un permission boundary limita el maximo de permisos efectivos aunque
  la politica de identidad sea muy amplia (seccion "Permission boundaries").
- `policies/mfa-enforcement.json`: como se fuerza a un usuario a configurar
  MFA antes de poder hacer cualquier otra cosa (seccion "Enforcement de MFA
  via Politica").

El script corre 8 casos de prueba (IP permitida vs bloqueada, accion dentro
y fuera del boundary, accion con y sin MFA) y verifica que el resultado
coincide con lo que AWS IAM resolveria en cada caso.

Es una forma de entender la logica de evaluacion **sin necesitar una
cuenta de AWS real** ni gastar en llamadas de API: las mismas politicas
JSON del post, evaluadas de forma determinista.

## Requisitos

- Python 3.8 o superior (sin dependencias de terceros, solo libreria
  estandar: `json`, `fnmatch`, `ipaddress`).

## Como correrlo

```bash
cd iam-cloud-gestion-identidades-acceso
python3 policy_simulator.py
```

## Salida esperada

```
=== 1. Least privilege S3 (policies/least-privilege-s3.json) ===
[OK] GetObject desde IP de la VPC (10.1.2.3) -> permitido: esperado=Allow obtenido=Allow
[OK] GetObject desde IP publica (203.0.113.5) -> denegado por condicion: esperado=Deny obtenido=Deny
[OK] DeleteObject desde la VPC -> denegado (accion no otorgada): esperado=Deny obtenido=Deny

=== 2. Permission boundary (policies/permission-boundary.json) ===
[OK] Rol con politica amplia + boundary: s3:PutObject -> permitido (dentro del boundary): esperado=Allow obtenido=Allow
[OK] Rol con politica amplia + boundary: iam:CreateUser -> denegado (fuera del boundary): esperado=Deny obtenido=Deny

=== 3. MFA enforcement (policies/mfa-enforcement.json) ===
[OK] s3:GetObject sin MFA -> denegado (DenyAllExceptMFASetup aplica): esperado=Deny obtenido=Deny
[OK] iam:CreateVirtualMFADevice sin MFA -> permitido (excepcion via NotAction): esperado=Allow obtenido=Allow
[OK] s3:GetObject con MFA presente -> el deny de este statement ya no aplica: esperado=Deny obtenido=Deny

RESULTADO: todas las verificaciones pasaron correctamente.
```

El script termina con exit code `0` cuando las 8 verificaciones pasan, y
`1` si alguna difiere de lo esperado (util para engancharlo en un pipeline
de CI que valide cambios a las politicas JSON).

## Estructura

```
iam-cloud-gestion-identidades-acceso/
├── README.md
├── policy_simulator.py               # motor de evaluacion + casos de prueba
└── policies/
    ├── least-privilege-s3.json       # politica de solo lectura con condicion de IP
    ├── permission-boundary.json      # boundary que limita el maximo de permisos
    ├── broad-identity-policy.json    # politica de identidad amplia (para probar el boundary)
    └── mfa-enforcement.json          # politica que fuerza configurar MFA
```

## Notas

- No usa cuentas ni recursos de AWS reales: es un modelo simplificado del
  algoritmo de evaluacion de politicas de AWS IAM, pensado para fines
  didacticos. No reemplaza `aws iam simulate-principal-policy` ni AWS IAM
  Access Analyzer para validar politicas de produccion.
- El simulador soporta los operadores de condicion usados en el post:
  `IpAddress`, `StringEquals` y `BoolIfExists`. Si necesitas extenderlo con
  otros operadores (`DateGreaterThan`, `ArnEquals`, etc.), agregalos en la
  funcion `_condition_matches` de `policy_simulator.py`.
