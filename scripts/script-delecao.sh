#!/usr/bin/env bash
# Remove toda a infraestrutura AWS criada pelo Terraform deste projeto.
# Uso: chmod +x scripts/script-delecao.sh && ./scripts/script-delecao.sh
#      ./scripts/script-delecao.sh --auto-approve

set -euo pipefail

AUTO_APPROVE=false
if [[ "${1:-}" == "--auto-approve" ]]; then
  AUTO_APPROVE=true
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT}/terraform"
TFVARS="${TF_DIR}/terraform.tfvars"

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

empty_s3_bucket() {
  local bucket="$1"
  local region="$2"

  if ! aws s3api head-bucket --bucket "$bucket" --region "$region" 2>/dev/null; then
    echo "  Bucket ${bucket} nao encontrado (ignorando)."
    return
  fi

  echo "  Esvaziando s3://${bucket} ..."
  aws s3 rm "s3://${bucket}" --recursive --region "$region" || true

  local key_marker="" version_marker=""
  while true; do
    local resp
    resp="$(aws s3api list-object-versions \
      --bucket "$bucket" \
      --region "$region" \
      ${key_marker:+--key-marker "$key_marker"} \
      ${version_marker:+--version-id-marker "$version_marker"} \
      --output json 2>/dev/null || echo '{}')"

    local count
    count="$(echo "$resp" | jq '[.Versions[]?, .DeleteMarkers[]?] | length')"
    if [[ "$count" -eq 0 ]]; then
      break
    fi

    echo "$resp" | jq -c '{
      Objects: ([.Versions[]?, .DeleteMarkers[]?] | map({Key, VersionId})),
      Quiet: true
    }' | aws s3api delete-objects --bucket "$bucket" --region "$region" --delete file:///dev/stdin

    key_marker="$(echo "$resp" | jq -r '.NextKeyMarker // empty')"
    version_marker="$(echo "$resp" | jq -r '.NextVersionIdMarker // empty')"
    if [[ -z "$key_marker" && -z "$version_marker" ]]; then
      break
    fi
  done
}

command -v aws >/dev/null 2>&1 || { echo "AWS CLI nao encontrado."; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "Terraform nao encontrado."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq nao encontrado (necessario para buckets versionados)."; exit 1; }
[[ -f "$TFVARS" ]] || { echo "Arquivo nao encontrado: ${TFVARS}"; exit 1; }

PROJECT_NAME="$(read_tfvar project_name yolo-violence)"
ENVIRONMENT="$(read_tfvar environment prod)"
BUCKET_SUFFIX="$(read_tfvar bucket_suffix "")"
AWS_REGION="$(read_tfvar aws_region us-east-1)"

NAME_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"
ECR_REPO="${NAME_PREFIX}-app"
BUCKETS=(
  #"${PROJECT_NAME}-input-${BUCKET_SUFFIX}"
  "${PROJECT_NAME}-predict-${BUCKET_SUFFIX}"
  "${PROJECT_NAME}-output-${BUCKET_SUFFIX}"
)

echo ""
echo "=== Script de delecao (infra AWS + Terraform) ==="
echo "Regiao:        ${AWS_REGION}"
echo "Prefixo:       ${NAME_PREFIX}"
echo "ECR:           ${ECR_REPO}"
echo "Buckets S3:"
for b in "${BUCKETS[@]}"; do echo "  - ${b}"; done
echo "Terraform:     ${TF_DIR}"
echo ""

read -r -p "Digite DELETAR para confirmar a remocao de TODOS esses recursos: " CONFIRM
if [[ "$CONFIRM" != "DELETAR" ]]; then
  echo "Operacao cancelada."
  exit 0
fi

echo ""
echo "[1/4] Parando tarefas ECS em execucao (se houver)..."
CLUSTER="${NAME_PREFIX}-cluster"
TASKS="$(aws ecs list-tasks --cluster "$CLUSTER" --region "$AWS_REGION" --desired-status RUNNING --query 'taskArns[]' --output text 2>/dev/null || true)"
if [[ -n "$TASKS" && "$TASKS" != "None" ]]; then
  for task in $TASKS; do
    echo "  Parando ${task}"
    aws ecs stop-task --cluster "$CLUSTER" --task "$task" --region "$AWS_REGION" >/dev/null
  done
  sleep 10
else
  echo "  Nenhuma tarefa em execucao."
fi

echo ""
echo "[2/4] Esvaziando buckets S3..."
for bucket in "${BUCKETS[@]}"; do
  empty_s3_bucket "$bucket" "$AWS_REGION"
done

echo ""
echo "[3/4] Removendo repositorio ECR (imagens Docker)..."
if aws ecr delete-repository --repository-name "$ECR_REPO" --force --region "$AWS_REGION" 2>/dev/null; then
  echo "  ECR ${ECR_REPO} removido."
else
  echo "  ECR ${ECR_REPO} nao encontrado ou ja removido."
fi

echo ""
echo "[4/4] Terraform destroy..."
cd "$TF_DIR"
terraform init -input=false
if [[ "$AUTO_APPROVE" == true ]]; then
  terraform destroy -auto-approve
else
  terraform destroy
fi

echo ""
echo "Concluido. Verifique no console AWS se restou algum recurso com tag ManagedBy=terraform."
