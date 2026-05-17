# Copie para terraform.tfvars (não commite segredos).
aws_region    = "us-east-1"
project_name  = "yolo-violence"
environment   = "prod"
bucket_suffix = "fiap-posttech-iadevs-tcfase04" # vazio = sufixo aleatório

# Chave padrão do objeto de entrada (pode ficar vazio e passar só no RunTask)
default_s3_input_key = ""

# GitHub Actions com OIDC (opcional)
github_oidc_enabled = true
# Formato org/repo (sem https://) - exigido pelo claim sub do OIDC do GitHub
github_repository = "brunojose1977/fiap-tech-challenger-fase4"

# Recursos Fargate (YOLO + OpenCV: CPU/memória maiores reduzem OOM)
fargate_cpu    = 4096
fargate_memory = 8192
