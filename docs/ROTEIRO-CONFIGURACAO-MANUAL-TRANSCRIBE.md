# Roteiro de configuração manual — Amazon Transcribe + ChatGPT

Siga esta ordem na **primeira** implantação do fluxo `aws-transcribe-audio-from-video-conversations`.

## 1. Terraform (AWS)

1. Em `terraform/terraform.tfvars`, confirme:
   - `transcribe_input_bucket_suffix = "fiap-posttech-iadevs-tcfase04"`
   - `transcribe_output_bucket_suffix = "fiap-posttech-iadevs-tcfase0"`
2. Execute:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```
3. Anote os outputs:
   ```bash
   terraform output -raw s3_transcribe_input_bucket
   terraform output -raw s3_transcribe_output_bucket
   ```

## 2. Conta OpenAI (ChatGPT API)

1. Acesse [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. Crie uma API key com permissão de uso do modelo configurado (`gpt-5.4` ou substitua por um modelo disponível na sua conta, ex. `gpt-4o`).
3. **Não** commite a chave no repositório.

## 3. Secrets no GitHub

Em **Settings → Secrets and variables → Actions → Repository secrets**:

| Secret | Valor |
|--------|--------|
| `AWS_ROLE_ARN` | ARN da role OIDC (output `github_actions_role_arn` após `github_oidc_enabled = true`) |
| `OPENAI_API_KEY` | Chave da API OpenAI (`sk-...`) |

Secrets opcionais (se os buckets Terraform forem diferentes dos padrões do workflow):

| Secret | Valor |
|--------|--------|
| `TRANSCRIBE_S3_INPUT_BUCKET` | Nome exato do bucket de entrada |
| `TRANSCRIBE_S3_OUTPUT_BUCKET` | Nome exato do bucket de saída |

> O workflow já define os buckets `transcribe-violence-input-fiap-posttech-iadevs-tcfase04` e `transcribe-violence-output-fiap-posttech-iadevs-tcfase0`. Ajuste o arquivo `.github/workflows/aws-transcribe-audio-from-video-conversations.yml` se os nomes reais divergirem.

## 4. Habilitar OIDC (se ainda não estiver)

No `terraform.tfvars`:

```hcl
github_oidc_enabled = true
github_repository   = "sua-org/seu-repo"
```

`terraform apply` e configure `AWS_ROLE_ARN` com o ARN retornado.

## 5. Upload de mídias

Envie vídeos/áudios para o bucket de entrada (ex.: `aws s3 cp conversa.mp4 s3://transcribe-violence-input-fiap-posttech-iadevs-tcfase04/`).

Formatos suportados: mp3, mp4, wav, flac, ogg, amr, webm, m4a, mov, mkv, mpeg.

## 6. Executar o pipeline

1. GitHub → **Actions** → **aws-transcribe-audio-from-video-conversations** → **Run workflow**.
2. Ao concluir, verifique no bucket de saída:
   - `transcribed-text-<nome-original>.txt`
   - `ChatGPT-5.4-avaliacao-conteudo-<nome-original>.pdf`

## 7. Execução local (opcional)

```powershell
$env:AWS_REGION="us-east-1"
$env:TRANSCRIBE_S3_INPUT_BUCKET="transcribe-violence-input-fiap-posttech-iadevs-tcfase04"
$env:TRANSCRIBE_S3_OUTPUT_BUCKET="transcribe-violence-output-fiap-posttech-iadevs-tcfase0"
$env:OPENAI_API_KEY="sk-..."
pip install -e ".[dev,transcribe]"
yolo-transcribe --log-level INFO
```

## 8. ECS Fargate (opcional)

Para rodar no Fargate, injete `OPENAI_API_KEY` via override do `run-task` (ou AWS Secrets Manager). Use a task family `ecs_transcribe_task_definition_family` e o container `transcribe-analyze`.
