data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  name_prefix           = "${var.project_name}-${var.environment}"
  bucket_suffix_final   = var.bucket_suffix != "" ? var.bucket_suffix : random_id.suffix.hex
  ecr_image             = "${aws_ecr_repository.app.repository_url}:${var.ecr_image_tag}"
  container_name        = "yolo-violence"
  cloudwatch_log_prefix = "/ecs/${local.name_prefix}"

  vpc_id            = var.create_dedicated_vpc ? aws_vpc.project[0].id : data.aws_vpc.default[0].id
  public_subnet_ids = var.create_dedicated_vpc ? aws_subnet.public[*].id : local.default_public_subnet_ids
}
