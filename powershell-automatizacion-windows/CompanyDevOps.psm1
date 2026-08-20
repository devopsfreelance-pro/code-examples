<#
    Modulo de ejemplo: CompanyDevOps.psm1

    Demuestra el patron central del post: un modulo PowerShell que encapsula
    un despliegue IDEMPOTENTE (verifica el estado actual antes de actuar) en
    lugar de una coleccion de scripts sueltos.

    El "sistema" gestionado es un archivo JSON local (deployments-state.json)
    que simula el estado real de una aplicacion desplegada, para poder
    ejecutar el ejemplo sin depender de Azure ni de ningun servicio externo.
#>

function Get-EnvironmentConfiguration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('Development', 'Staging', 'Production')]
        [string]$Environment
    )

    # En un caso real esto vendria de Azure App Configuration, un archivo
    # por entorno, o un servicio interno. Aqui se devuelve una configuracion
    # fija por entorno para mantener el ejemplo autocontenido.
    $configs = @{
        Development = @{ ReplicaCount = 1; HealthCheckPath = '/healthz' }
        Staging     = @{ ReplicaCount = 2; HealthCheckPath = '/healthz' }
        Production  = @{ ReplicaCount = 3; HealthCheckPath = '/healthz' }
    }

    return $configs[$Environment]
}

function Test-DeploymentPrerequisites {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Config
    )

    if (-not $Config.ContainsKey('ReplicaCount')) {
        throw 'La configuracion no define ReplicaCount'
    }

    Write-Verbose 'Prerequisitos de despliegue validados correctamente'
}

function Get-DeploymentStatePath {
    # Centraliza la ruta del archivo de estado para que todas las funciones
    # del modulo lean/escriban siempre el mismo lugar.
    return Join-Path -Path $PSScriptRoot -ChildPath 'deployments-state.json'
}

function Get-CurrentDeploymentState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationName,

        [Parameter(Mandatory = $true)]
        [string]$Environment
    )

    $statePath = Get-DeploymentStatePath
    if (-not (Test-Path $statePath)) {
        return $null
    }

    $allState = Get-Content -Path $statePath -Raw | ConvertFrom-Json
    $key = "$ApplicationName/$Environment"

    if ($allState.PSObject.Properties.Name -contains $key) {
        return $allState.$key
    }

    return $null
}

function Set-CurrentDeploymentState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationName,

        [Parameter(Mandatory = $true)]
        [string]$Environment,

        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    $statePath = Get-DeploymentStatePath
    $allState = [ordered]@{}

    if (Test-Path $statePath) {
        $existing = Get-Content -Path $statePath -Raw | ConvertFrom-Json
        foreach ($prop in $existing.PSObject.Properties) {
            $allState[$prop.Name] = $prop.Value
        }
    }

    $key = "$ApplicationName/$Environment"
    $allState[$key] = [ordered]@{
        Version     = $Version
        DeployedAt  = (Get-Date -Format 'o')
    }

    ($allState | ConvertTo-Json -Depth 5) | Set-Content -Path $statePath -Encoding utf8
}

function Invoke-ApplicationDeployment {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [hashtable]$Config,

        [Parameter(Mandatory = $true)]
        [string]$Version,

        [Parameter(Mandatory = $true)]
        [string]$Environment
    )

    Write-Host "Desplegando $Name version $Version en $Environment ($($Config.ReplicaCount) replicas)..."
    Set-CurrentDeploymentState -ApplicationName $Name -Environment $Environment -Version $Version
}

function Test-ApplicationHealth {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Environment
    )

    $state = Get-CurrentDeploymentState -ApplicationName $Name -Environment $Environment
    if ($null -eq $state) {
        throw "No se encontro estado de despliegue para $Name en $Environment"
    }

    Write-Host "Health check OK: $Name@$($state.Version) esta activo en $Environment"
}

function Deploy-Application {
    <#
        .SYNOPSIS
        Despliega una aplicacion de forma idempotente: si la version pedida
        ya esta desplegada en el entorno, no hace nada; si no, despliega y
        actualiza el estado.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationName,

        [Parameter(Mandatory = $true)]
        [ValidateSet('Development', 'Staging', 'Production')]
        [string]$Environment,

        [Parameter(Mandatory = $false)]
        [string]$Version = 'latest'
    )

    Write-Verbose "Iniciando despliegue de $ApplicationName en $Environment"

    $config = Get-EnvironmentConfiguration -Environment $Environment
    Test-DeploymentPrerequisites -Config $config

    $currentState = Get-CurrentDeploymentState -ApplicationName $ApplicationName -Environment $Environment

    if ($null -ne $currentState -and $currentState.Version -eq $Version) {
        Write-Host "$ApplicationName ya esta en la version $Version en $Environment. No se requiere accion (idempotente)."
    }
    else {
        Invoke-ApplicationDeployment -Name $ApplicationName -Config $config -Version $Version -Environment $Environment
    }

    Test-ApplicationHealth -Name $ApplicationName -Environment $Environment
}

Export-ModuleMember -Function Deploy-Application, Get-EnvironmentConfiguration, `
    Test-DeploymentPrerequisites, Get-CurrentDeploymentState, Set-CurrentDeploymentState, `
    Invoke-ApplicationDeployment, Test-ApplicationHealth
