<#
    Script de demostracion: ejecuta Deploy-Application dos veces seguidas
    con la misma version para mostrar la idempotencia del modulo.

    Primera corrida: no existe estado previo -> despliega.
    Segunda corrida: la version ya coincide -> no hace nada, solo valida salud.
#>

$ErrorActionPreference = 'Stop'

$modulePath = Join-Path -Path $PSScriptRoot -ChildPath 'CompanyDevOps.psm1'
Import-Module $modulePath -Force

# Limpiar estado de corridas anteriores para que la demo sea reproducible
$statePath = Join-Path -Path $PSScriptRoot -ChildPath 'deployments-state.json'
if (Test-Path $statePath) {
    Remove-Item $statePath
}

Write-Host "=== Primera ejecucion (debe desplegar) ===" -ForegroundColor Cyan
Deploy-Application -ApplicationName 'inventory-api' -Environment 'Staging' -Version '1.4.2' -Verbose

Write-Host ""
Write-Host "=== Segunda ejecucion, misma version (debe ser idempotente) ===" -ForegroundColor Cyan
Deploy-Application -ApplicationName 'inventory-api' -Environment 'Staging' -Version '1.4.2' -Verbose

Write-Host ""
Write-Host "=== Estado final persistido ===" -ForegroundColor Cyan
Get-Content -Path $statePath | Write-Host
