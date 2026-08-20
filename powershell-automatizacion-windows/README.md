# PowerShell DevOps: modulo de despliegue idempotente

Ejemplo de codigo para el post [PowerShell DevOps: Automatización Windows en Entornos Modernos](https://www.devopsfreelance.pro/blog/posts/powershell-automatizacion-windows/).

## Que demuestra

El post explica dos ideas centrales sobre PowerShell en pipelines DevOps:

1. Encapsular logica en un **modulo** (`.psm1`) con funciones Verbo-Sustantivo, en vez de scripts sueltos.
2. Escribir despliegues **idempotentes**: antes de actuar, se verifica el estado actual; si ya coincide con lo deseado, no se hace nada.

Este ejemplo implementa exactamente el modulo `CompanyDevOps.psm1` esbozado en el post (`Deploy-Application`, `Test-DeploymentPrerequisites`, `Invoke-ApplicationDeployment`, `Test-ApplicationHealth`), pero funcional de punta a punta: el "sistema" desplegado es un archivo JSON local (`deployments-state.json`) que actua como estado persistido, para poder correr el ejemplo en cualquier maquina sin depender de Azure ni de IIS.

- `CompanyDevOps.psm1` — el modulo con la logica de despliegue idempotente.
- `run-demo.ps1` — corre `Deploy-Application` dos veces con la misma version para mostrar que la segunda corrida no hace nada.
- `Deploy.Tests.ps1` — pruebas con Pester (el framework de testing que menciona el post) que verifican la idempotencia.

No incluye el ejemplo de Azure Key Vault ni el de PowerShell DSC del post porque ambos requieren una suscripcion de Azure o un host Windows con IIS; el patron de idempotencia es el concepto que se puede demostrar realmente en minutos y sin cuentas de pago.

## Requisitos

- Docker (para correr PowerShell Core sin instalar nada en el sistema). Se usa la imagen oficial `mcr.microsoft.com/powershell`.
- Alternativa sin Docker: PowerShell 7+ (`pwsh`) instalado localmente ([instrucciones de Microsoft](https://learn.microsoft.com/powershell/scripting/install/installing-powershell)).

No se requiere cuenta de Azure ni ningun otro servicio de pago.

## Pasos para correrlo

### Opcion A: con Docker (recomendado)

Desde este directorio:

```bash
docker run --rm -v "$(pwd):/app" -w /app mcr.microsoft.com/powershell:latest \
  pwsh -NoProfile -Command "./run-demo.ps1"
```

### Opcion B: con pwsh instalado localmente

```bash
pwsh -NoProfile -File ./run-demo.ps1
```

### Salida esperada

```
=== Primera ejecucion (debe desplegar) ===
VERBOSE: Iniciando despliegue de inventory-api en Staging
VERBOSE: Prerequisitos de despliegue validados correctamente
Desplegando inventory-api version 1.4.2 en Staging (2 replicas)...
Health check OK: inventory-api@1.4.2 esta activo en Staging

=== Segunda ejecucion, misma version (debe ser idempotente) ===
VERBOSE: Iniciando despliegue de inventory-api en Staging
VERBOSE: Prerequisitos de despliegue validados correctamente
inventory-api ya esta en la version 1.4.2 en Staging. No se requiere accion (idempotente).
Health check OK: inventory-api@1.4.2 esta activo en Staging

=== Estado final persistido ===
{
  "inventory-api/Staging": {
    "Version": "1.4.2",
    "DeployedAt": "2026-08-20T15:22:08.7000884+00:00"
  }
}
```

En la segunda ejecucion, el mensaje cambia de "Desplegando..." a "...no se requiere accion (idempotente)": esa es la parte que ilustra el concepto del post.

`run-demo.ps1` borra `deployments-state.json` al empezar para que la demo sea reproducible en cada corrida; ese archivo se genera solo, no forma parte del repositorio.

## Correr las pruebas Pester (opcional)

```bash
docker run --rm -v "$(pwd):/app" -w /app mcr.microsoft.com/powershell:latest \
  pwsh -NoProfile -Command "Install-Module -Name Pester -Force -Scope CurrentUser -RequiredVersion 5.6.1 -SkipPublisherCheck; Invoke-Pester -Path ./Deploy.Tests.ps1 -Output Detailed"
```

Salida esperada: `Tests Passed: 5, Failed: 0`.

Nota: se fija `-RequiredVersion 5.6.1` porque la imagen `mcr.microsoft.com/powershell:latest` trae PowerShell 7.4.2, y Pester 6.x mas reciente requiere una version de `System.Management.Automation` mas nueva; Pester 5.6.1 es compatible y es la version que usa el post como referencia.
