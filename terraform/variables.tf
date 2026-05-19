variable "aws_region" {
  type        = string
  description = "Região AWS (ex.: us-east-1)."
  default     = "us-east-1"
}

variable "create_dedicated_vpc" {
  type        = bool
  description = "Se true, cria uma VPC pública mínima (2 AZs) para Fargate — use quando a conta não tiver VPC default. Se false, usa a VPC default da região."
  default     = true
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR da VPC criada quando create_dedicated_vpc é true (evite sobrepor redes existentes na sua conta/VPN)."
  default     = "10.20.0.0/16"
}

variable "project_name" {
  type        = string
  description = "Prefixo lógico para recursos."
  default     = "yolo-violence"
}

variable "transcribe_project_name" {
  type        = string
  description = "Prefixo dos buckets S3 do fluxo Amazon Transcribe (entrada/saída)."
  default     = "transcribe-violence"
}

variable "transcribe_input_bucket_suffix" {
  type        = string
  description = "Sufixo do bucket de entrada Transcribe (ex.: fiap-posttech-iadevs-tcfase04)."
  default     = "fiap-posttech-iadevs-tcfase04"
}

variable "transcribe_output_bucket_suffix" {
  type        = string
  description = "Sufixo do bucket de saída Transcribe (ex.: fiap-posttech-iadevs-tcfase0)."
  default     = "fiap-posttech-iadevs-tcfase0"
}

variable "environment" {
  type        = string
  description = "Ambiente (dev, staging, prod)."
  default     = "prod"
}

variable "bucket_suffix" {
  type        = string
  description = "Sufixo único global para nomes dos buckets S3. Se vazio, um sufixo aleatório é gerado."
  default     = ""
}

variable "default_s3_input_key" {
  type        = string
  description = "Chave padrão do objeto no bucket de entrada (pode ser sobrescrita no RunTask)."
  default     = ""
}

variable "ecr_image_tag" {
  type        = string
  description = "Tag da imagem publicada no ECR (CI/CD atualiza latest)."
  default     = "latest"
}

variable "fargate_cpu" {
  type        = number
  description = "Unidades de CPU Fargate (1024 = 1 vCPU)."
  default     = 4096
}

variable "fargate_memory" {
  type        = number
  description = "Memória MB para a tarefa Fargate."
  default     = 8192
}

variable "github_oidc_enabled" {
  type        = bool
  description = "Cria provedor OIDC e role para GitHub Actions fazer deploy."
  default     = false
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in format owner/repo"
  default     = ""

  validation {
    condition     = var.github_repository == "" || can(regex("^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$", var.github_repository))
    error_message = "Repository must be in format: owner/repo"
  }
}
