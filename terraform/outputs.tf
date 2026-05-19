output "s3_input_bucket" {
  value       = aws_s3_bucket.input.bucket
  description = "Bucket de vídeos de entrada."
}

output "s3_predict_bucket" {
  value       = aws_s3_bucket.predict.bucket
  description = "Bucket com saída bruta do predict (YOLO)."
}

output "s3_output_bucket" {
  value       = aws_s3_bucket.output.bucket
  description = "Bucket com vídeo anotado (violência placeholder)."
}

output "s3_transcribe_input_bucket" {
  value       = aws_s3_bucket.transcribe_input.bucket
  description = "Bucket de entrada do fluxo Amazon Transcribe."
}

output "s3_transcribe_output_bucket" {
  value       = aws_s3_bucket.transcribe_output.bucket
  description = "Bucket de saída do fluxo Amazon Transcribe."
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.app.repository_url
  description = "URL do repositório ECR para docker push."
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.this.name
  description = "Nome do cluster ECS Fargate."
}

output "ecs_task_definition_family" {
  value       = aws_ecs_task_definition.app.family
  description = "Family da task definition (usar com run-task)."
}

output "ecs_task_container_name" {
  value       = local.container_name
  description = "Nome do container na task (para overrides)."
}

output "vpc_id" {
  value       = local.vpc_id
  description = "VPC usada pelo security group da task ECS."
}

output "default_subnet_ids" {
  value       = local.public_subnet_ids
  description = "Subnets para networkConfiguration do RunTask (públicas na VPC dedicada, ou subnets da VPC default)."
}

output "ecs_subnet_ids_csv" {
  value       = join(",", local.public_subnet_ids)
  description = "IDs das subnets separados por vírgula (valor do secret GitHub ECS_SUBNET_IDS)."
}

output "ecs_task_security_group_id" {
  value       = aws_security_group.task.id
  description = "Security group da tarefa (para networkConfiguration do RunTask)."
}

output "github_actions_role_arn" {
  value       = try(aws_iam_role.github_actions[0].arn, null)
  description = "ARN da role OIDC para GitHub Actions (se habilitada)."
}

output "ecs_transcribe_task_definition_family" {
  value       = aws_ecs_task_definition.transcribe.family
  description = "Family da task definition do fluxo Transcribe + ChatGPT."
}

output "ecs_transcribe_container_name" {
  value       = "transcribe-analyze"
  description = "Nome do container Transcribe na task ECS."
}
