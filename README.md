# Pipeline YOLOv8 Pose + S3 (produção)

Este repositório extrai a lógica do notebook Colab `yolov8_pose_colab_v3_detecção_da_violencia_integração_AWS_S3_1_2.ipynb` para um **pacote Python** executável em container, com **infraestrutura como código (Terraform)** na AWS (S3, ECR, ECS Fargate) e **CI/CD** no GitHub Actions.

> **Segurança:** se você já versionou credenciais AWS em arquivos locais (por exemplo `configuração_pastas.txt`), **revogue essas chaves no IAM** e use apenas perfis locais (`aws configure`), variáveis de ambiente em CI ou **IAM roles** (ECS task role / OIDC no GitHub). O arquivo `configuração_pastas.txt` está no `.gitignore` deste projeto.

---

## O que o pipeline faz (passo a passo)

1. **Entrada:** lê a chave `S3_INPUT_KEY` no bucket `S3_INPUT_BUCKET` e baixa o vídeo para um diretório de trabalho (`WORK_DIR`).
2. **Modelo:** carrega o Ultralytics YOLO (`MODEL_NAME`, padrão `yolov8n-pose.pt`).
3. **Predict:** executa `model.predict` com `save=True`, gera o vídeo intermediário na pasta de runs do YOLO e **envia** esse arquivo para `S3_PREDICT_BUCKET`.
4. **Anotação “violência”:** percorre o vídeo frame a frame com `save=False`, aplica a função placeholder `is_violence_detected` (mesma ideia do notebook) e grava um MP4 com aviso visual quando a heurística dispara.
5. **Saída:** envia o MP4 final para `S3_OUTPUT_BUCKET`.

A aplicação segue o padrão **12-factor**: toda configuração vem de **variáveis de ambiente** (não há segredos no código).

---

## Estrutura do repositório

| Caminho | Função |
|--------|--------|
| `src/yolo_violence_pipeline/` | Código de produção (`config`, `s3_io`, `violence`, `pipeline`, `cli`) |
| `tests/` | Testes unitários (rápidos, sem baixar pesos YOLO) |
| `terraform/` | IaC: buckets S3, ECR, IAM, ECS Fargate (VPC padrão) |
| `Dockerfile` | Imagem de runtime com Python 3.11 e dependências de vídeo |
| `.github/workflows/ci-cd.yml` | CI (testes, Ruff, build Docker, Terraform validate) e CD manual |
| `scripts/run_local.ps1` / `run_local.sh` | Execução local com `.env` (instala `[dev,runtime]`) |
| `scripts/docker_run.sh` | Build da imagem e `docker run --env-file .env` |

---

## Requisitos locais

- **Python 3.11+** (recomendado 3.11 em Linux/macOS/Windows com caminhos longos habilitados se for instalar PyTorch).
- **Docker** (para build da imagem).
- **Terraform** ≥ 1.5 (para provisionar a AWS).
- **AWS CLI** autenticado na conta alvo.

Dependências de **runtime** (YOLO + OpenCV) estão no extra opcional `[runtime]` do `pyproject.toml`. Os testes em CI usam apenas `[dev]` para serem leves.

---

## Configuração rápida (local)

1. Copie o exemplo de ambiente:

   ```bash
   cp .env.example .env
   ```

2. Ajuste buckets e chave do objeto (valores alinhados ao output do Terraform).

3. **Windows (PowerShell):**

   ```powershell
   .\scripts\run_local.ps1
   ```

4. **Linux/macOS:**

   ```bash
   chmod +x scripts/run_local.sh
   ./scripts/run_local.sh
   ```

Na AWS (ECS), as credenciais vêm automaticamente da **task role** — não configure `AWS_ACCESS_KEY_ID` no container.

---

## Infraestrutura (Terraform)

### Passo a passo

1. Entre na pasta `terraform` e copie variáveis:

   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   ```

   Edite `bucket_suffix` para um valor **únio globalmente** (nomes de bucket S3 são únicos na AWS). Se deixar vazio, um sufixo aleatório é gerado.

2. Inicialize e aplique:

   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. Faça o **primeiro push** da imagem para o ECR (o ECS precisa de uma imagem existente). Use o output `ecr_repository_url`:

   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t yolo-violence:latest ..
   docker tag yolo-violence:latest <ecr_repository_url>:latest
   docker push <ecr_repository_url>:latest
   ```

4. Após mudanças na imagem com a tag `latest`, o ECS pode continuar usando uma revisão antiga da task definition. Opções: rode `terraform apply` de novo (ajuste `ecr_image_tag` se usar tags imutáveis) ou registre uma nova revisão apontando para o digest desejado.

5. **Executar uma tarefa** (processamento pontual no Fargate):

   - Defina `S3_INPUT_KEY` (via override do `run-task` ou variável `default_s3_input_key` no Terraform).
   - Use os outputs `ecs_cluster_name`, `ecs_task_definition_family`, `default_subnet_ids`, `ecs_task_security_group_id`.

   Exemplo de override (conceitual): variável de ambiente `S3_INPUT_KEY` no container.

### OIDC do GitHub (opcional)

No `terraform.tfvars`, defina:

```hcl
github_oidc_enabled = true
github_repository   = "sua-org/seu-repo"
```

Isso cria o provedor OIDC (se ainda não existir na conta) e uma role para o Actions fazer push no ECR e `RunTask`. Se o provedor `token.actions.githubusercontent.com` já existir, importe-o ou ajuste o Terraform conforme a política da sua empresa.

---

## CI/CD (GitHub Actions)

| Gatilho | Comportamento |
|--------|----------------|
| **Pull request / push em `main`** | Ruff, Pytest, `docker build` (validação), `terraform fmt` + `init -backend=false` + `validate` |
| **workflow_dispatch** (“Run workflow”) | Passos opcionais: push da imagem para o ECR e, se configurado, `RunTask` no Fargate |

### Secrets recomendados (CD manual)

- `AWS_ROLE_ARN` — role assumível via OIDC com permissão de ECR + ECS.
- `ECR_REPOSITORY_NAME` — nome do repositório (não a URL completa), igual ao resource Terraform.
- Para `RunTask`: `ECS_CLUSTER_NAME`, `ECS_TASK_DEFINITION_FAMILY`, `ECS_CONTAINER_NAME` (output `ecs_task_container_name`), `ECS_SUBNET_IDS` (use `terraform output -raw ecs_subnet_ids_csv`), `ECS_SECURITY_GROUP_ID` (`terraform output -raw ecs_task_security_group_id`).

> Se a tarefa ficar em **PENDING**, quase sempre é rede: subnets sem rota para Internet (IGW) ou `ECS_SUBNET_IDS` / `ECS_SECURITY_GROUP_ID` desatualizados após `terraform apply`. Rode `terraform output -raw ecs_subnet_ids_csv` e atualize o secret no GitHub.

---

## Diagrama da infraestrutura

```mermaid
flowchart TB
  subgraph aws["AWS Cloud"]
    subgraph s3["Amazon S3"]
      B1["Bucket entrada\n(S3_INPUT_BUCKET)"]
      B2["Bucket predict\n(S3_PREDICT_BUCKET)"]
      B3["Bucket saída\n(S3_OUTPUT_BUCKET)"]
    end
    subgraph ecr["Amazon ECR"]
      IMG["Imagem Docker\nyolo-violence"]
    end
    subgraph ecs["Amazon ECS Fargate"]
      TASK["Task pontual\nyolo-violence process"]
    end
    CW["CloudWatch Logs"]
    IAM["IAM Roles\ntask + execução"]
    GH["GitHub Actions\n(OIDC)"]
  end
  DEV["Desenvolvedor\nTerraform / CLI"]
  DEV --> B1
  DEV --> terraform["Terraform Apply"]
  terraform --> B1
  terraform --> B2
  terraform --> B3
  terraform --> ecr
  terraform --> ecs
  terraform --> IAM
  GH -->|"docker push"| IMG
  GH -->|"RunTask"| TASK
  IMG --> TASK
  IAM --> TASK
  TASK --> CW
  TASK -->|"GetObject"| B1
  TASK -->|"PutObject"| B2
  TASK -->|"PutObject"| B3
```

Fluxo de **dados**: vídeo sobe para o bucket de entrada → a tarefa Fargate baixa, processa, grava o intermediário no bucket de predict e o vídeo anotado no bucket de saída.

---

## GPU e performance

A task Fargate definida aqui usa **CPU** apenas. Para inferência mais rápida ou modelos maiores, avalie **EC2 com GPU**, **AWS Batch** com AMI GPU ou **Amazon SageMaker** — o mesmo container pode servir de base, mudando apenas o orquestrador e o tipo de instância.

---

## Comandos úteis

```bash
# Testes e lint (sem YOLO)
pip install -e ".[dev]"
python -m pytest
python -m ruff check src tests

# CLI (com variáveis de ambiente definidas)
pip install -e ".[dev,runtime]"
yolo-violence process --log-level INFO
```

---

## Licença

MIT (ajuste conforme a política da sua organização).
