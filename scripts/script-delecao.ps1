# Remove toda a infraestrutura AWS criada pelo Terraform deste projeto.
# Uso: .\scripts\script-delecao.ps1
#      .\scripts\script-delecao.ps1 -AutoApprove   # sem confirmação do terraform destroy
#
# Pré-requisitos: AWS CLI autenticado, Terraform instalado, terraform.tfvars em terraform/

param(
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$tfDir = Join-Path $root "terraform"
$tfvarsPath = Join-Path $tfDir "terraform.tfvars"

function Read-TfVar {
    param([string]$Name, [string]$Default)
    if (-not (Test-Path $tfvarsPath)) {
        return $Default
    }
    $line = Get-Content $tfvarsPath | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -First 1
    if (-not $line) {
        return $Default
    }
    if ($line -match '=\s*(.+?)(?:\s+#.*)?$') {
        return $Matches[1].Trim().Trim('"')
    }
    return $Default
}

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Clear-S3Bucket {
    param([string]$Bucket, [string]$Region)

    if (-not $Bucket) { return }

    try {
        aws s3api head-bucket --bucket $Bucket --region $Region 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Bucket $Bucket nao encontrado (ignorando)."
            return
        }
    } catch {
        Write-Host "  Bucket $Bucket nao encontrado (ignorando)."
        return
    }

    Write-Host "  Esvaziando s3://$Bucket ..."
    aws s3 rm "s3://$Bucket" --recursive --region $Region

    $keyMarker = ""
    $versionMarker = ""
    do {
        $args = @(
            "s3api", "list-object-versions",
            "--bucket", $Bucket,
            "--region", $Region,
            "--output", "json"
        )
        if ($keyMarker) {
            $args += @("--key-marker", $keyMarker)
            if ($versionMarker) { $args += @("--version-id-marker", $versionMarker) }
        }
        $json = aws @args
        if ($LASTEXITCODE -ne 0) { break }

        $data = $json | ConvertFrom-Json
        $entries = @()
        if ($data.Versions) { $entries += $data.Versions }
        if ($data.DeleteMarkers) { $entries += $data.DeleteMarkers }

        if ($entries.Count -gt 0) {
            $objects = $entries | ForEach-Object {
                @{ Key = $_.Key; VersionId = $_.VersionId }
            }
            $payload = @{ Objects = $objects; Quiet = $true } | ConvertTo-Json -Compress -Depth 5
            $tmp = New-TemporaryFile
            [System.IO.File]::WriteAllText($tmp.FullName, $payload)
            aws s3api delete-objects --bucket $Bucket --region $Region --delete "file://$($tmp.FullName)"
            Remove-Item $tmp -Force
        }

        $keyMarker = $data.NextKeyMarker
        $versionMarker = $data.NextVersionIdMarker
    } while ($keyMarker -or $versionMarker)
}

# --- inicio ---

if (-not (Test-CommandExists "aws")) {
    Write-Error "AWS CLI nao encontrado. Instale e configure: aws configure"
}
if (-not (Test-CommandExists "terraform")) {
    Write-Error "Terraform nao encontrado."
}
if (-not (Test-Path $tfvarsPath)) {
    Write-Error "Arquivo nao encontrado: $tfvarsPath"
}

$projectName = Read-TfVar "project_name" "yolo-violence"
$environment = Read-TfVar "environment" "prod"
$bucketSuffix = Read-TfVar "bucket_suffix" ""
$awsRegion = Read-TfVar "aws_region" "us-east-1"

$namePrefix = "$projectName-$environment"
$ecrRepo = "$namePrefix-app"
$buckets = @(
    "$projectName-input-$bucketSuffix",
    "$projectName-predict-$bucketSuffix",
    "$projectName-output-$bucketSuffix"
)

Write-Host ""
Write-Host "=== Script de delecao (infra AWS + Terraform) ===" -ForegroundColor Cyan
Write-Host "Regiao:        $awsRegion"
Write-Host "Prefixo:       $namePrefix"
Write-Host "ECR:           $ecrRepo"
Write-Host "Buckets S3:"
foreach ($b in $buckets) { Write-Host "  - $b" }
Write-Host "Terraform:     $tfDir"
Write-Host ""

$confirm = Read-Host "Digite DELETAR para confirmar a remocao de TODOS esses recursos"
if ($confirm -ne "DELETAR") {
    Write-Host "Operacao cancelada."
    exit 0
}

Write-Host ""
Write-Host "[1/4] Parando tarefas ECS em execucao (se houver)..." -ForegroundColor Yellow
$cluster = "$namePrefix-cluster"
$tasks = aws ecs list-tasks --cluster $cluster --region $awsRegion --desired-status RUNNING --query "taskArns[]" --output text 2>$null
if ($tasks -and $tasks -ne "None") {
    foreach ($task in $tasks -split "\s+") {
        if ($task) {
            Write-Host "  Parando $task"
            aws ecs stop-task --cluster $cluster --task $task --region $awsRegion | Out-Null
        }
    }
    Start-Sleep -Seconds 10
} else {
    Write-Host "  Nenhuma tarefa em execucao."
}

Write-Host ""
Write-Host "[2/4] Esvaziando buckets S3..." -ForegroundColor Yellow
foreach ($bucket in $buckets) {
    Clear-S3Bucket -Bucket $bucket -Region $awsRegion
}

Write-Host ""
Write-Host "[3/4] Removendo repositorio ECR (imagens Docker)..." -ForegroundColor Yellow
aws ecr delete-repository --repository-name $ecrRepo --force --region $awsRegion 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ECR $ecrRepo removido."
} else {
    Write-Host "  ECR $ecrRepo nao encontrado ou ja removido."
}

Write-Host ""
Write-Host "[4/4] Terraform destroy..." -ForegroundColor Yellow
Set-Location $tfDir
terraform init -input=false
if ($AutoApprove) {
    terraform destroy -auto-approve
} else {
    terraform destroy
}

Write-Host ""
Write-Host "Concluido. Verifique no console AWS se restou algum recurso com tag ManagedBy=terraform." -ForegroundColor Green
