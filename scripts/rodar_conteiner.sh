#!/usr/bin/env bash
# Executa o pipeline no ECS Fargate (imagem do ECR via task definition do Terraform).
#
# Uso:
#   chmod +x scripts/rodar_conteiner.sh
#   ./scripts/rodar_conteiner.sh
#   ./scripts/rodar_conteiner.sh meu-video.mp4
#   ./scripts/rodar_conteiner.sh meu-video.mp4 --apply
#   ./scripts/rodar_conteiner.sh --build-push meu-video.mp4 --apply
#
# Flags:
#   --apply       Roda "terraform apply" antes do RunTask (atualiza task definition com imagem ECR)
#   --build-push  Build local, tag e push para o ECR (requer Docker e login no ECR)
#   --no-wait     Nao aguarda a tarefa terminar (so inicia o RunTask)

set -euo pipefail

S3_INPUT_KEY=""
DO_APPLY=false
DO_BUILD_PUSH=false
DO_WAIT=true

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      DO_APPLY=true
      shift
      ;;
    --build-push)
      DO_BUILD_PUSH=true
      shift
      ;;
    --no-wait)
      DO_WAIT=false
      shift
      ;;
    -h|--help)
      usage 0
      ;;
    --*)
      echo "Argumento desconhecido: $1" >&2
      exit 1
      ;;
    *)
      if [[ -z "$S3_INPUT_KEY" ]]; then
        S3_INPUT_KEY="$1"
        shift
      else
        echo "Argumento desconhecido: $1" >&2
        exit 1
      fi
      ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "$1 nao encontrado." >&2
    exit 1
  fi
}

read_tfvar() {
  local name="$1"
  local default="$2"
  if [[ ! -f "$TFVARS" ]]; then
    echo "$default"
    return
  fi
  local line
  line="$(grep -E "^[[:space:]]*${name}[[:space:]]*=" "$TFVARS" | head -n1 || true)"
  if [[ -z "$line" ]]; then
    echo "$default"
    return
  fi
  echo "$line" | sed -E 's/^[^=]+=[[:space:]]*"?([^"#]+)"?.*/\1/' | tr -d ' "'
}

require_cmd aws
require_cmd terraform
require_cmd jq

if [[ ! -f "$TFVARS" ]]; then
  echo "Arquivo nao encontrado: $TFVARS" >&2
  echo "Copie terraform.tfvars.example para terraform.tfvars" >&2
  exit 1
fi

AWS_REGION="$(read_tfvar aws_region us-east-1)"
PROJECT_NAME="$(read_tfvar project_name yolo-violence)"
ENVIRONMENT="$(read_tfvar environment prod)"
ECR_IMAGE_TAG="$(read_tfvar ecr_image_tag latest)"

NAME_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"
CLUSTER="${NAME_PREFIX}-cluster"
TASK_DEF_FAMILY="${NAME_PREFIX}-task"
CONTAINER="yolo-violence"
LOG_GROUP="/ecs/${NAME_PREFIX}/yolo-violence"

if [[ -z "$S3_INPUT_KEY" ]]; then
  read -r -p "Chave S3 do video no bucket de entrada (S3_INPUT_KEY): " S3_INPUT_KEY
fi
if [[ -z "$S3_INPUT_KEY" ]]; then
  echo "S3_INPUT_KEY e obrigatorio." >&2
  exit 1
fi

echo
echo "=== Rodar container no ECS Fargate ==="
echo "Regiao:              ${AWS_REGION}"
echo "Cluster:             ${CLUSTER}"
echo "Task definition:     ${TASK_DEF_FAMILY}"
echo "Container:           ${CONTAINER}"
echo "S3_INPUT_KEY:        ${S3_INPUT_KEY}"
echo

cd "$TF_DIR"
terraform init -input=false >/dev/null

echo "[1/6] Lendo outputs do Terraform..."
CLUSTER="$(terraform output -raw ecs_cluster_name)"
TASK_DEF_FAMILY="$(terraform output -raw ecs_task_definition_family)"
CONTAINER="$(terraform output -raw ecs_task_container_name)"
SECURITY_GROUP="$(terraform output -raw ecs_task_security_group_id)"
ECR_URL="$(terraform output -raw ecr_repository_url)"
S3_INPUT_BUCKET="$(terraform output -raw s3_input_bucket)"
S3_PREDICT_BUCKET="$(terraform output -raw s3_predict_bucket)"
S3_OUTPUT_BUCKET="$(terraform output -raw s3_output_bucket)"
SUBNETS_JSON="$(terraform output -json default_subnet_ids)"

if [[ -z "$SECURITY_GROUP" || "$SUBNETS_JSON" == "null" || "$SUBNETS_JSON" == "[]" ]]; then
  echo "Falha ao obter subnets ou security group. Rode terraform apply antes." >&2
  exit 1
fi

echo "  Cluster:          ${CLUSTER}"
echo "  Task definition:  ${TASK_DEF_FAMILY}"
echo "  Container:        ${CONTAINER}"
echo "  Security group:   ${SECURITY_GROUP}"
echo "  ECR:              ${ECR_URL}:${ECR_IMAGE_TAG}"
echo "  Bucket entrada:   ${S3_INPUT_BUCKET}"
echo "  Bucket predict:   ${S3_PREDICT_BUCKET}"
echo "  Bucket saida:     ${S3_OUTPUT_BUCKET}"
echo

if [[ "$DO_BUILD_PUSH" == true ]]; then
  echo "[2/6] Build e push da imagem para o ECR..."
  require_cmd docker
  cd "$ROOT"
  aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin "$ECR_URL"
  docker build -t yolo-violence:local .
  docker tag "yolo-violence:local" "${ECR_URL}:${ECR_IMAGE_TAG}"
  docker push "${ECR_URL}:${ECR_IMAGE_TAG}"
  echo "  Imagem enviada: ${ECR_URL}:${ECR_IMAGE_TAG}"
  echo
  cd "$TF_DIR"
else
  echo "[2/6] Build/push ignorado (use --build-push para enviar imagem ao ECR)."
  echo "  Comandos manuais:"
  echo "    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URL}"
  echo "    docker build -t yolo-violence:local ${ROOT}"
  echo "    docker tag yolo-violence:local ${ECR_URL}:${ECR_IMAGE_TAG}"
  echo "    docker push ${ECR_URL}:${ECR_IMAGE_TAG}"
  echo
fi

if [[ "$DO_APPLY" == true ]]; then
  echo "[3/6] Terraform apply (atualiza task definition com a imagem do ECR)..."
  terraform apply -input=false
  echo
else
  echo "[3/6] Terraform apply ignorado (use --apply apos push de nova imagem :latest)."
  echo "  Comando: cd terraform && terraform apply"
  echo
fi

echo "[4/6] Iniciando tarefa Fargate (aws ecs run-task)..."

NETWORK_CONFIG="$(jq -n \
  --argjson subnets "$SUBNETS_JSON" \
  --arg sg "$SECURITY_GROUP" \
  '{awsvpcConfiguration: {subnets: $subnets, securityGroups: [$sg], assignPublicIp: "ENABLED"}}')"

OVERRIDES="$(jq -n \
  --arg name "$CONTAINER" \
  --arg key "$S3_INPUT_KEY" \
  '{containerOverrides: [{name: $name, environment: [{name: "S3_INPUT_KEY", value: $key}]}]}')"

RUN_JSON="$(aws ecs run-task \
  --region "$AWS_REGION" \
  --cluster "$CLUSTER" \
  --launch-type FARGATE \
  --task-definition "$TASK_DEF_FAMILY" \
  --network-configuration "$NETWORK_CONFIG" \
  --overrides "$OVERRIDES" \
  --output json)"

TASK_ARN="$(echo "$RUN_JSON" | jq -r '.tasks[0].taskArn // empty')"
if [[ -z "$TASK_ARN" ]]; then
  echo "RunTask nao retornou taskArn. Verifique falhas no cluster/capacidade." >&2
  echo "$RUN_JSON" | jq . >&2 || echo "$RUN_JSON" >&2
  exit 1
fi

echo "  Task ARN: ${TASK_ARN}"
echo

if [[ "$DO_WAIT" == false ]]; then
  echo "[5/6] Aguardar conclusao ignorado (--no-wait)."
else
  echo "[5/6] Aguardando conclusao da tarefa..."
  while true; do
    sleep 15
    TASK_STATUS="$(aws ecs describe-tasks \
      --region "$AWS_REGION" \
      --cluster "$CLUSTER" \
      --tasks "$TASK_ARN" \
      --query "tasks[0].lastStatus" \
      --output text 2>/dev/null || true)"
    EXIT_CODE="$(aws ecs describe-tasks \
      --region "$AWS_REGION" \
      --cluster "$CLUSTER" \
      --tasks "$TASK_ARN" \
      --query "tasks[0].containers[0].exitCode" \
      --output text 2>/dev/null || true)"
    STOP_REASON="$(aws ecs describe-tasks \
      --region "$AWS_REGION" \
      --cluster "$CLUSTER" \
      --tasks "$TASK_ARN" \
      --query "tasks[0].stoppedReason" \
      --output text 2>/dev/null || true)"

    echo "  Status: ${TASK_STATUS}  ExitCode: ${EXIT_CODE}"

    case "$TASK_STATUS" in
      RUNNING|PENDING|PROVISIONING)
        continue
        ;;
      STOPPED)
        if [[ "$EXIT_CODE" != "0" && "$EXIT_CODE" != "None" && -n "$EXIT_CODE" ]]; then
          echo
          echo "Tarefa finalizou com erro. ExitCode=${EXIT_CODE} Motivo=${STOP_REASON}" >&2
          exit 1
        fi
        break
        ;;
      *)
        break
        ;;
    esac
  done
fi

echo "[6/6] Comandos uteis para acompanhar:"
echo
echo "  aws ecs describe-tasks --region ${AWS_REGION} --cluster ${CLUSTER} --tasks ${TASK_ARN}"
echo "  aws logs tail ${LOG_GROUP} --follow --region ${AWS_REGION}"
echo
echo "Dentro do container o CMD executa: yolo-violence process"
echo "Resultados esperados nos buckets predict e output do Terraform."
echo
