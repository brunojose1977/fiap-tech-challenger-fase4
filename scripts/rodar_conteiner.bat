@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Executa o pipeline no ECS Fargate (imagem do ECR via task definition do Terraform).
REM
REM Uso:
REM   scripts\rodar_conteiner.bat
REM   scripts\rodar_conteiner.bat meu-video.mp4
REM   scripts\rodar_conteiner.bat meu-video.mp4 --apply
REM   scripts\rodar_conteiner.bat --build-push meu-video.mp4 --apply
REM
REM Flags:
REM   --apply       Roda "terraform apply" antes do RunTask (atualiza task definition com imagem ECR)
REM   --build-push  Build local, tag e push para o ECR (requer Docker e login no ECR)
REM   --no-wait     Nao aguarda a tarefa terminar (so inicia o RunTask)

set "S3_INPUT_KEY="
set "DO_APPLY=0"
set "DO_BUILD_PUSH=0"
set "DO_WAIT=1"

:ParseArgs
if "%~1"=="" goto ArgsDone
if /i "%~1"=="--apply" (
  set "DO_APPLY=1"
  shift
  goto ParseArgs
)
if /i "%~1"=="--build-push" (
  set "DO_BUILD_PUSH=1"
  shift
  goto ParseArgs
)
if /i "%~1"=="--no-wait" (
  set "DO_WAIT=0"
  shift
  goto ParseArgs
)
if not defined S3_INPUT_KEY (
  set "S3_INPUT_KEY=%~1"
  shift
  goto ParseArgs
)
echo Argumento desconhecido: %~1
exit /b 1

:ArgsDone
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
  echo Copie terraform.tfvars.example para terraform.tfvars
  exit /b 1
)

call :ReadTfVar aws_region us-east-1 AWS_REGION
call :ReadTfVar project_name yolo-violence PROJECT_NAME
call :ReadTfVar environment prod ENVIRONMENT
call :ReadTfVar ecr_image_tag latest ECR_IMAGE_TAG

set "NAME_PREFIX=%PROJECT_NAME%-%ENVIRONMENT%"
set "ECR_REPO=%NAME_PREFIX%-app"
set "CLUSTER=%NAME_PREFIX%-cluster"
set "TASK_DEF_FAMILY=%NAME_PREFIX%-task"
set "CONTAINER=yolo-violence"
set "LOG_GROUP=/ecs/%NAME_PREFIX%/yolo-violence"

if not defined S3_INPUT_KEY (
  set /p S3_INPUT_KEY=Chave S3 do video no bucket de entrada (S3_INPUT_KEY):
)
if "!S3_INPUT_KEY!"=="" (
  echo S3_INPUT_KEY e obrigatorio.
  exit /b 1
)

echo.
echo === Rodar container no ECS Fargate ===
echo Regiao:              %AWS_REGION%
echo Cluster:             %CLUSTER%
echo Task definition:     %TASK_DEF_FAMILY%
echo Container:           %CONTAINER%
echo S3_INPUT_KEY:        !S3_INPUT_KEY!
echo.

pushd "%TF_DIR%"
terraform init -input=false >nul
if errorlevel 1 (
  echo Falha em: terraform init
  popd
  exit /b 1
)

echo [1/6] Lendo outputs do Terraform...
for /f "delims=" %%V in ('terraform output -raw ecs_cluster_name 2^>nul') do set "CLUSTER=%%V"
for /f "delims=" %%V in ('terraform output -raw ecs_task_definition_family 2^>nul') do set "TASK_DEF_FAMILY=%%V"
for /f "delims=" %%V in ('terraform output -raw ecs_task_container_name 2^>nul') do set "CONTAINER=%%V"
for /f "delims=" %%V in ('terraform output -raw ecs_task_security_group_id 2^>nul') do set "SECURITY_GROUP=%%V"
for /f "delims=" %%V in ('terraform output -raw ecr_repository_url 2^>nul') do set "ECR_URL=%%V"
for /f "delims=" %%V in ('terraform output -raw s3_input_bucket 2^>nul') do set "S3_INPUT_BUCKET=%%V"
for /f "delims=" %%V in ('terraform output -raw s3_predict_bucket 2^>nul') do set "S3_PREDICT_BUCKET=%%V"
for /f "delims=" %%V in ('terraform output -raw s3_output_bucket 2^>nul') do set "S3_OUTPUT_BUCKET=%%V"

set "SUBNETS_JSON_FILE=%TEMP%\yolo_subnets_%RANDOM%.json"
terraform output -json default_subnet_ids > "!SUBNETS_JSON_FILE!" 2>nul
if not exist "!SUBNETS_JSON_FILE!" (
  echo Falha ao obter default_subnet_ids. Rode terraform apply antes.
  popd
  exit /b 1
)

if "!SECURITY_GROUP!"=="" (
  echo Falha ao obter ecs_task_security_group_id.
  popd
  exit /b 1
)

echo   Cluster:          !CLUSTER!
echo   Task definition:  !TASK_DEF_FAMILY!
echo   Container:        !CONTAINER!
echo   Security group:   !SECURITY_GROUP!
echo   ECR:              !ECR_URL!:!ECR_IMAGE_TAG!
echo   Bucket entrada:   !S3_INPUT_BUCKET!
echo   Bucket predict:   !S3_PREDICT_BUCKET!
echo   Bucket saida:     !S3_OUTPUT_BUCKET!
echo.

if "!DO_BUILD_PUSH!"=="1" (
  echo [2/6] Build e push da imagem para o ECR...
  where docker >nul 2>&1 || (
    echo Docker nao encontrado.
    popd
    exit /b 1
  )
  pushd "%ROOT%"
  for /f "delims=" %%P in ('aws ecr get-login-password --region %AWS_REGION%') do set "ECR_PASS=%%P"
  echo !ECR_PASS!| docker login --username AWS --password-stdin "!ECR_URL!" >nul
  if errorlevel 1 (
    echo Falha no login do ECR.
    popd
    popd
    exit /b 1
  )
  docker build -t yolo-violence:local .
  if errorlevel 1 (
    popd
    popd
    exit /b 1
  )
  docker tag yolo-violence:local "!ECR_URL!:!ECR_IMAGE_TAG!"
  docker push "!ECR_URL!:!ECR_IMAGE_TAG!"
  if errorlevel 1 (
    popd
    popd
    exit /b 1
  )
  popd
  echo   Imagem enviada: !ECR_URL!:!ECR_IMAGE_TAG!
  echo.
) else (
  echo [2/6] Build/push ignorado (use --build-push para enviar imagem ao ECR).
  echo   Comandos manuais:
  echo     aws ecr get-login-password --region %AWS_REGION% ^| docker login --username AWS --password-stdin !ECR_URL!
  echo     docker build -t yolo-violence:local %ROOT%
  echo     docker tag yolo-violence:local !ECR_URL!:!ECR_IMAGE_TAG!
  echo     docker push !ECR_URL!:!ECR_IMAGE_TAG!
  echo.
)

if "!DO_APPLY!"=="1" (
  echo [3/6] Terraform apply (atualiza task definition com a imagem do ECR)...
  terraform apply -input=false
  if errorlevel 1 (
    popd
    exit /b 1
  )
  echo.
) else (
  echo [3/6] Terraform apply ignorado (use --apply apos push de nova imagem :latest).
  echo   Comando: cd terraform ^&^& terraform apply
  echo.
)

echo [4/6] Iniciando tarefa Fargate (aws ecs run-task)...

set "NET_CFG_FILE=%TEMP%\yolo_net_%RANDOM%.json"
set "OVERRIDES_FILE=%TEMP%\yolo_over_%RANDOM%.json"
set "RUN_OUT_FILE=%TEMP%\yolo_run_%RANDOM%.json"

where jq >nul 2>&1
if errorlevel 1 (
  echo jq nao encontrado. Instale jq ou use Git Bash com o comando do README.
  del "!SUBNETS_JSON_FILE!" 2>nul
  popd
  exit /b 1
)

jq -n --slurpfile subnets "!SUBNETS_JSON_FILE!" --arg sg "!SECURITY_GROUP!" ^
  "{awsvpcConfiguration: {subnets: $subnets[0], securityGroups: [$sg], assignPublicIp: \"ENABLED\"}}" ^
  > "!NET_CFG_FILE!"

jq -n --arg name "!CONTAINER!" --arg key "!S3_INPUT_KEY!" ^
  "{containerOverrides: [{name: $name, environment: [{name: \"S3_INPUT_KEY\", value: $key}]}]}" ^
  > "!OVERRIDES_FILE!"

set "NET_URI=!NET_CFG_FILE:\=/!"
set "OVR_URI=!OVERRIDES_FILE:\=/!"

aws ecs run-task ^
  --region "%AWS_REGION%" ^
  --cluster "!CLUSTER!" ^
  --launch-type FARGATE ^
  --task-definition "!TASK_DEF_FAMILY!" ^
  --network-configuration "file://!NET_URI!" ^
  --overrides "file://!OVR_URI!" ^
  --output json > "!RUN_OUT_FILE!"

set "RUN_EXIT=!ERRORLEVEL!"
del "!NET_CFG_FILE!" 2>nul
del "!OVERRIDES_FILE!" 2>nul
del "!SUBNETS_JSON_FILE!" 2>nul

if not "!RUN_EXIT!"=="0" (
  echo Falha em aws ecs run-task.
  type "!RUN_OUT_FILE!" 2>nul
  del "!RUN_OUT_FILE!" 2>nul
  popd
  exit /b 1
)

for /f "delims=" %%T in ('jq -r ".tasks[0].taskArn // empty" "!RUN_OUT_FILE!"') do set "TASK_ARN=%%T"
del "!RUN_OUT_FILE!" 2>nul

if "!TASK_ARN!"=="" (
  echo RunTask nao retornou taskArn. Verifique falhas no cluster/capacidade.
  popd
  exit /b 1
)

echo   Task ARN: !TASK_ARN!
echo.

if "!DO_WAIT!"=="0" (
  echo [5/6] Aguardar conclusao ignorado (--no-wait).
  goto ShowFollowUp
)

echo [5/6] Aguardando conclusao da tarefa...
:WaitLoop
timeout /t 15 /nobreak >nul
for /f "delims=" %%S in ('aws ecs describe-tasks --region "%AWS_REGION%" --cluster "!CLUSTER!" --tasks "!TASK_ARN!" --query "tasks[0].lastStatus" --output text 2^>nul') do set "TASK_STATUS=%%S"
for /f "delims=" %%S in ('aws ecs describe-tasks --region "%AWS_REGION%" --cluster "!CLUSTER!" --tasks "!TASK_ARN!" --query "tasks[0].containers[0].exitCode" --output text 2^>nul') do set "EXIT_CODE=%%S"
for /f "delims=" %%S in ('aws ecs describe-tasks --region "%AWS_REGION%" --cluster "!CLUSTER!" --tasks "!TASK_ARN!" --query "tasks[0].stoppedReason" --output text 2^>nul') do set "STOP_REASON=%%S"

echo   Status: !TASK_STATUS!  ExitCode: !EXIT_CODE!

if /i "!TASK_STATUS!"=="RUNNING" goto WaitLoop
if /i "!TASK_STATUS!"=="PENDING" goto WaitLoop
if /i "!TASK_STATUS!"=="PROVISIONING" goto WaitLoop

if /i "!TASK_STATUS!"=="STOPPED" (
  if not "!EXIT_CODE!"=="0" if not "!EXIT_CODE!"=="None" (
    echo.
    echo Tarefa finalizou com erro. ExitCode=!EXIT_CODE! Motivo=!STOP_REASON!
    popd
    exit /b 1
  )
)

:ShowFollowUp
echo [6/6] Comandos uteis para acompanhar:
echo.
echo   aws ecs describe-tasks --region %AWS_REGION% --cluster !CLUSTER! --tasks !TASK_ARN!
echo   aws logs tail !LOG_GROUP! --follow --region %AWS_REGION%
echo.
echo Dentro do container o CMD executa: yolo-violence process
echo Resultados esperados nos buckets predict e output do Terraform.
echo.

popd
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
