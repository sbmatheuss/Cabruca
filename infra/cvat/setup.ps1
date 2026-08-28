<#
Bootstrap do CVAT self-hosted para anotacao do dataset CABRUCA (ADR 0012).
Nao vendoriza a config do CVAT -- so automatiza os comandos ja documentados
em dataset/README.md: clone da tag fixada + docker compose up.
#>

param(
    [string]$CvatVersion = "v2.72.0",
    # REVISAR: destino default e uma pasta irma do repo (fora do Cabruca).
    # Ajuste com -TargetDir se preferir outro caminho.
    [string]$TargetDir = (Join-Path (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))) "cvat")
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TargetDir)) {
    Write-Host "Clonando CVAT $CvatVersion em $TargetDir..."
    git clone -b $CvatVersion https://github.com/cvat-ai/cvat $TargetDir
} else {
    Write-Host "CVAT ja clonado em $TargetDir, pulando clone."
}

Push-Location $TargetDir
try {
    Write-Host "Subindo docker compose..."
    docker compose up -d
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "CVAT no ar em http://localhost:8080"
Write-Host "Crie o superuser manualmente (pede usuario/senha interativos):"
Write-Host "  docker exec -it cvat_server bash -ic 'python3 ~/manage.py createsuperuser'"
Write-Host ""
Write-Host "Para encerrar depois:"
Write-Host "  cd `"$TargetDir`"; docker compose down"
