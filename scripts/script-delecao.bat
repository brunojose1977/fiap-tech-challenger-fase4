@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Remove toda a infraestrutura AWS criada pelo Terraform deste projeto.
REM Uso: scripts\script-delecao.bat
REM      scripts\script-delecao.bat --auto-approve

set "AUTO_APPROVE=0"
if /i "%~1"=="--auto-approve" set "AUTO_APPROVE=1"

set "ROOT=%~dp0.."
set "TF_DIR=%ROOT%\terraform"
set "TFVARS=%TF_DIR%\terraform.tfvars"

where aws >nul 2>&1 || (
  echo AWS CLI nao encontrado. Instale e configure: aws configure
  exit /b 1
)
where terraform >nul 2>&1 || (
  echo Terraform nao encontrado.
  exit /b 1
)
if not exist "%TFVARS%" (
  echo Arquivo nao encontrado: %TFVARS%
  exit /b 1
)

call :ReadTfVar project_name yolo-violence PROJECT_NAME
call :ReadTfVar environment prod ENVIRONMENT
call :ReadTfVar bucket_suffix "" BUCKET_SUFFIX
call :ReadTfVar aws_region us-east-1 AWS_REGION

set "NAME_PREFIX=%PROJECT_NAME%-%ENVIRONMENT%"
set "ECR_REPO=%NAME_PREFIX%-app"
set "CLUSTER=%NAME_PREFIX%-cluster"

echo.
echo === Script de delecao (infra AWS + Terraform) ===
echo Regiao:        %AWS_REGION%
echo Prefixo:       %NAME_PREFIX%
echo ECR:           %ECR_REPO%
echo Buckets S3:
REM echo   - %PROJECT_NAME%-input-%BUCKET_SUFFIX%
echo   - %PROJECT_NAME%-predict-%BUCKET_SUFFIX%
echo   - %PROJECT_NAME%-output-%BUCKET_SUFFIX%
echo Terraform:     %TF_DIR%
echo.

set /p CONFIRM=Digite DELETAR para confirmar a remocao de TODOS esses recursos:
if /i not "!CONFIRM!"=="DELETAR" (
  echo Operacao cancelada.
  exit /b 0
)

echo.
echo [1/4] Parando tarefas ECS em execucao (se houver)...
set "HAS_TASKS=0"
for /f "tokens=*" %%L in ('aws ecs list-tasks --cluster "%CLUSTER%" --region "%AWS_REGION%" --desired-status RUNNING --query "taskArns[]" --output text 2^>nul') do (
  if not "%%L"=="" if /i not "%%L"=="None" (
    set "HAS_TASKS=1"
    for %%T in (%%L) do (
      echo   Parando %%T
      aws ecs stop-task --cluster "%CLUSTER%" --task "%%T" --region "%AWS_REGION%" >nul 2>&1
    )
  )
)
if "!HAS_TASKS!"=="1" (
  timeout /t 10 /nobreak >nul
) else (
  echo   Nenhuma tarefa em execucao.
)


echo.
echo [3/4] Removendo repositorio ECR (imagens Docker)...
aws ecr delete-repository --repository-name "%ECR_REPO%" --force --region "%AWS_REGION%" >nul 2>&1
if !ERRORLEVEL! equ 0 (
  echo   ECR %ECR_REPO% removido.
) else (
  echo   ECR %ECR_REPO% nao encontrado ou ja removido.
)

echo.
echo [4/4] Terraform destroy...
pushd "%TF_DIR%"
terraform init -input=false
if "%AUTO_APPROVE%"=="1" (
  terraform destroy -auto-approve
) else (
  terraform destroy
)
set "TF_EXIT=!ERRORLEVEL!"
popd
if not "!TF_EXIT!"=="0" exit /b !TF_EXIT!

echo.
echo Concluido. Verifique no console AWS se restou algum recurso com tag ManagedBy=terraform.
exit /b 0

REM --- funcoes ---

:ReadTfVar
set "VAR_NAME=%~1"
set "VAR_DEFAULT=%~2"
set "VAR_OUT=%~3"
set "VAR_VALUE=%VAR_DEFAULT%"
for /f "usebackq tokens=1* delims==" %%A in (`findstr /r /c:"^[ ]*%VAR_NAME%[ ]*=" "%TFVARS%" 2^>nul`) do (
  set "LINE=%%B"
  set "LINE=!LINE:#*=!"
  for /f "tokens=* delims= " %%V in ("!LINE!") do set "VAR_VALUE=%%~V"
  set "VAR_VALUE=!VAR_VALUE:"=!"
)
set "%VAR_OUT%=%VAR_VALUE%"
exit /b 0

:EmptyS3Bucket
set "BUCKET=%~1"
aws s3api head-bucket --bucket "%BUCKET%" --region "%AWS_REGION%" >nul 2>&1
if errorlevel 1 (
  echo   Bucket %BUCKET% nao encontrado (ignorando).
  exit /b 0
)

echo   Esvaziando s3://%BUCKET% ...
aws s3 rm "s3://%BUCKET%" --recursive --region "%AWS_REGION%" >nul 2>&1

where jq >nul 2>&1
if errorlevel 1 (
  echo   AVISO: jq nao encontrado; objetos versionados podem impedir o destroy. Instale jq ou esvazie o bucket no console.
  exit /b 0
)

set "KEY_MARKER="
set "VERSION_MARKER="
:EmptyS3Loop
set "VER_FILE=%TEMP%\s3ver_%RANDOM%.json"
set "DEL_FILE=%TEMP%\s3del_%RANDOM%.json"

if defined KEY_MARKER (
  if defined VERSION_MARKER (
    aws s3api list-object-versions --bucket "%BUCKET%" --region "%AWS_REGION%" --output json --key-marker "!KEY_MARKER!" --version-id-marker "!VERSION_MARKER!" > "!VER_FILE!" 2>nul
  ) else (
    aws s3api list-object-versions --bucket "%BUCKET%" --region "%AWS_REGION%" --output json --key-marker "!KEY_MARKER!" > "!VER_FILE!" 2>nul
  )
) else (
  aws s3api list-object-versions --bucket "%BUCKET%" --region "%AWS_REGION%" --output json > "!VER_FILE!" 2>nul
)
if not exist "!VER_FILE!" exit /b 0

for /f %%C in ('jq "[.Versions[]?, .DeleteMarkers[]?] | length" "!VER_FILE!" 2^>nul') do set "COUNT=%%C"
if not defined COUNT set "COUNT=0"
if "!COUNT!"=="0" (
  del "!VER_FILE!" 2>nul
  exit /b 0
)

jq -c "{Objects: ([.Versions[]?, .DeleteMarkers[]?] | map({Key, VersionId})), Quiet: true}" "!VER_FILE!" > "!DEL_FILE!"
set "DEL_URI=!DEL_FILE:\=/!"
aws s3api delete-objects --bucket "%BUCKET%" --region "%AWS_REGION%" --delete "file://!DEL_URI!" >nul 2>&1

set "KEY_MARKER="
set "VERSION_MARKER="
for /f "delims=" %%K in ('jq -r ".NextKeyMarker // empty" "!VER_FILE!" 2^>nul') do set "KEY_MARKER=%%K"
for /f "delims=" %%V in ('jq -r ".NextVersionIdMarker // empty" "!VER_FILE!" 2^>nul') do set "VERSION_MARKER=%%V"
del "!VER_FILE!" 2>nul
del "!DEL_FILE!" 2>nul


#--------------- REPOSICIONAMENTO DA EXECUÇÃO DE DELEÇÃO DE S3 ------------------------------ 
echo.
echo [2/4] Esvaziando buckets S3...
REM call :EmptyS3Bucket "%PROJECT_NAME%-input-%BUCKET_SUFFIX%"
call :EmptyS3Bucket "%PROJECT_NAME%-predict-%BUCKET_SUFFIX%"
call :EmptyS3Bucket "%PROJECT_NAME%-output-%BUCKET_SUFFIX%"

#--------------- REPOSICIONAMENTO DA EXECUÇÃO DE DELEÇÃO DE S3 ------------------------------ 


if defined KEY_MARKER goto EmptyS3Loop
if defined VERSION_MARKER goto EmptyS3Loop
exit /b 0

