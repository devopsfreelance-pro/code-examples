<#
    Pruebas Pester para CompanyDevOps.psm1
    Corren en PowerShell Core (pwsh), sin dependencias de Azure.
#>

BeforeAll {
    $modulePath = Join-Path -Path $PSScriptRoot -ChildPath 'CompanyDevOps.psm1'
    Import-Module $modulePath -Force

    $script:statePath = Join-Path -Path $PSScriptRoot -ChildPath 'deployments-state.json'
    if (Test-Path $script:statePath) {
        Remove-Item $script:statePath
    }
}

AfterAll {
    if (Test-Path $script:statePath) {
        Remove-Item $script:statePath
    }
}

Describe 'Get-EnvironmentConfiguration' {
    It 'devuelve configuracion valida para Production' {
        $config = Get-EnvironmentConfiguration -Environment 'Production'
        $config.ReplicaCount | Should -Be 3
    }
}

Describe 'Deploy-Application (idempotencia)' {
    It 'despliega la aplicacion la primera vez' {
        Deploy-Application -ApplicationName 'demo-app' -Environment 'Development' -Version '1.0.0'
        $state = Get-CurrentDeploymentState -ApplicationName 'demo-app' -Environment 'Development'
        $state.Version | Should -Be '1.0.0'
    }

    It 'no cambia DeployedAt si se ejecuta de nuevo con la misma version' {
        $before = Get-CurrentDeploymentState -ApplicationName 'demo-app' -Environment 'Development'

        Start-Sleep -Milliseconds 50
        Deploy-Application -ApplicationName 'demo-app' -Environment 'Development' -Version '1.0.0'

        $after = Get-CurrentDeploymentState -ApplicationName 'demo-app' -Environment 'Development'
        $after.DeployedAt | Should -Be $before.DeployedAt
    }

    It 'actualiza el estado cuando cambia la version' {
        Deploy-Application -ApplicationName 'demo-app' -Environment 'Development' -Version '2.0.0'
        $state = Get-CurrentDeploymentState -ApplicationName 'demo-app' -Environment 'Development'
        $state.Version | Should -Be '2.0.0'
    }
}

Describe 'Test-DeploymentPrerequisites' {
    It 'lanza excepcion si falta ReplicaCount en la config' {
        { Test-DeploymentPrerequisites -Config @{} } | Should -Throw
    }
}
