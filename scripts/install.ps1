<#
.SYNOPSIS
    Instalador de Luna Builder Fast para Google Antigravity en Windows (PowerShell).
.DESCRIPTION
    Copia e instala el plugin, agentes, skills, hooks y herramientas en la configuración
    global de Antigravity (~/.gemini/config/plugins/luna-builder-fast) o en un workspace local.
.PARAMETER Workspace
    Ruta opcional a un proyecto para instalar como personalización de workspace.
.PARAMETER Uninstall
    Desinstala el plugin de la ubicación especificada.
.EXAMPLE
    .\install.ps1
    .\install.ps1 -Workspace "C:\Proyectos\MiApp"
    .\install.ps1 -Uninstall
#>

[CmdletBinding()]
param (
    [string]$Workspace = "",
    [switch]$Uninstall = $false
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot

if ($Workspace -ne "") {
    $TargetDir = Join-Path $Workspace ".agents\plugins\luna-builder-fast"
    $IsWorkspace = $true
} else {
    $TargetDir = Join-Path $env:USERPROFILE ".gemini\config\plugins\luna-builder-fast"
    $IsWorkspace = $false
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  INSTALADOR DE LUNA BUILDER FAST PARA GOOGLE ANTIGRAVITY" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Repositorio: $RepoRoot"
Write-Host "Destino:     $TargetDir"
Write-Host "-----------------------------------------------------------------"

if ($Uninstall) {
    if (Test-Path $TargetDir) {
        Remove-Item -Path $TargetDir -Recurse -Force
        Write-Host "[✓] Plugin desinstalado correctamente de $TargetDir" -ForegroundColor Green
    } else {
        Write-Host "[-] El plugin no está instalado en esa ubicación." -ForegroundColor Yellow
    }
    exit 0
}

# Crear directorio destino
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

$Items = @("plugin.json", "hooks.json", "README.md", "agents", "rules", "skills")

foreach ($item in $Items) {
    $src = Join-Path $RepoRoot $item
    $dest = Join-Path $TargetDir $item

    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dest -Recurse -Force
        Write-Host "[+] Copiado: $item" -ForegroundColor Green
    } else {
        Write-Host "[!] Advertencia: $item no encontrado en el repo" -ForegroundColor Yellow
    }
}

Write-Host "-----------------------------------------------------------------"
Write-Host "[✓] ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!" -ForegroundColor Green
Write-Host "================================================================="
if (-not $IsWorkspace) {
    Write-Host "Para aplicar los cambios:" -ForegroundColor Cyan
    Write-Host "  1. Reinicia Antigravity si estaba abierto para indexar el nuevo plugin."
    Write-Host "  2. En el chat, invoca Luna Fast con frases como:"
    Write-Host "     - 'Ejecuta esta tarea con luna fast'"
    Write-Host "     - 'Aplica este cambio en modo express'"
    Write-Host "     - 'Ejecuta estas tareas independientes en fan-out con luna fast'"
}
