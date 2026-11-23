<#
.SYNOPSIS
    Chatterbox AI Voice Studio - Windows Server Runner
.DESCRIPTION
    Launches the FastAPI REST server and web Voice Studio dashboard.
#>

[CmdletBinding()]
param(
    [string]$HostAddress = "0.0.0.0",
    [int]$Port = 8000,
    [switch]$Reload = $false
)

$env:PYTHONPATH = "$PSScriptRoot;$PSScriptRoot\plugins\chatterbox"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Starting Chatterbox Voice Studio Server            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Host: http://$HostAddress`:$Port" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:$Port/dashboard/index.html" -ForegroundColor Green
Write-Host "API Health: http://localhost:$Port/health" -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------"

$reloadFlag = ""
if ($Reload) {
    $reloadFlag = "--reload"
}

python -m uvicorn plugins.chatterbox.backend.server:app --host $HostAddress --port $Port $reloadFlag
