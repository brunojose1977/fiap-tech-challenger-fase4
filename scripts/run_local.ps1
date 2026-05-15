# Execução local do pipeline (PowerShell).
# Pré-requisitos: AWS CLI configurado (perfil ou variáveis), Docker opcional.
# Uso: copie .env.example para .env, preencha e rode: .\scripts\run_local.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not (Test-Path ".env")) {
    Write-Host "Crie o arquivo .env a partir de .env.example na raiz do projeto."
    exit 1
}

Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    $pair = $_ -split '=', 2
    if ($pair.Length -eq 2) {
        [System.Environment]::SetEnvironmentVariable($pair[0].Trim(), $pair[1].Trim(), "Process")
    }
}

pip install -e ".[dev,runtime]"
yolo-violence process --log-level INFO
