# Security gate con Policy-as-Code (OPA/Conftest)

Post relacionado: [7 Secretos para Dominar DevOps Seguridad en 2025](https://www.devopsfreelance.pro/blog/posts/seguridad-devops/)

## Que demuestra

El post explica que en un DevSecOps maduro la seguridad se convierte en **codigo
declarativo**: politicas versionadas en Git que bloquean automaticamente un
despliegue si no cumple reglas basicas (no correr como root, no privilegiado,
filesystem de solo lectura), en vez de depender de una revision manual.

Este ejemplo toma la politica Rego del post (seccion "Seguridad como Codigo") y
la corre de verdad con [Conftest](https://www.conftest.dev/) (basado en Open
Policy Agent) contra dos manifiestos de Kubernetes:

- `manifests/pod-insecure.yaml`: contenedor `privileged: true`, sin
  `runAsNonRoot` ni `readOnlyRootFilesystem` -> el gate lo **bloquea**.
- `manifests/pod-secure.yaml`: mismo contenedor pero con los tres controles de
  seguridad activados -> el gate lo **aprueba**.

Esto es exactamente el mecanismo de "gates" de seguridad que describe el post
en la seccion de Desafios (bloquear vs aprobar vs solo notificar), aplicado a
Infraestructura como Codigo.

## Requisitos

- Docker instalado y corriendo (no hace falta instalar OPA ni Conftest: se usa
  la imagen oficial `openpolicyagent/conftest`).

## Como correrlo

```bash
cd seguridad-devops
./run.sh
```

Tambien se puede invocar Conftest manualmente para ver el detalle:

```bash
# Manifiesto inseguro -> falla
docker run --rm -v "$(pwd)/policy:/project/policy" -v "$(pwd)/manifests:/project/manifests" \
  -w /project openpolicyagent/conftest:v0.55.0 test --policy policy manifests/pod-insecure.yaml

# Manifiesto seguro -> pasa
docker run --rm -v "$(pwd)/policy:/project/policy" -v "$(pwd)/manifests:/project/manifests" \
  -w /project openpolicyagent/conftest:v0.55.0 test --policy policy manifests/pod-secure.yaml
```

## Salida esperada

Para `pod-insecure.yaml`, Conftest devuelve 3 fallos y exit code distinto de 0:

```
FAIL - manifests/pod-insecure.yaml - main - Container app must not be privileged
FAIL - manifests/pod-insecure.yaml - main - Container app must run as non-root
FAIL - manifests/pod-insecure.yaml - main - Container app must use read-only root filesystem

3 tests, 0 passed, 0 warnings, 3 failures, 0 exceptions
```

Para `pod-secure.yaml`, Conftest reporta las 3 reglas pasadas y exit code 0:

```
3 tests, 3 passed, 0 warnings, 0 failures, 0 exceptions
```

`run.sh` corre ambos casos y termina con `OK` si el gate se comporto como se
espera (bloquea el inseguro, aprueba el seguro), o `FALLO` en caso contrario.

## Estructura

```
seguridad-devops/
├── policy/
│   └── kubernetes.rego     # Reglas Rego adaptadas del post (deny por falta de controles de seguridad)
├── manifests/
│   ├── pod-insecure.yaml   # Viola las 3 reglas
│   └── pod-secure.yaml     # Cumple las 3 reglas
└── run.sh                  # Corre el gate contra ambos manifiestos via Docker
```

## Llevarlo a un pipeline real

En CI/CD esto se integra como paso previo al `kubectl apply` / `helm upgrade`,
igual que en el ejemplo del post con Checkov: si Conftest devuelve exit code
distinto de 0, el pipeline falla y no se despliega. No requiere una cuenta ni
un servicio pago: corre 100% local/offline contra el archivo YAML.
