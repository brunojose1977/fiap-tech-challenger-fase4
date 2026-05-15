resource "aws_security_group" "task" {
  name_prefix = "${local.name_prefix}-task-"
  description = "Egress para S3/ECR/Internet (subnets publicas com IGW ou VPC default)."
  vpc_id      = local.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "${local.cloudwatch_log_prefix}/yolo-violence"
  retention_in_days = 14
}

resource "aws_ecs_cluster" "this" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${local.name_prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = local.container_name
      image     = local.ecr_image
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_INPUT_BUCKET", value = aws_s3_bucket.input.bucket },
        { name = "S3_PREDICT_BUCKET", value = aws_s3_bucket.predict.bucket },
        { name = "S3_OUTPUT_BUCKET", value = aws_s3_bucket.output.bucket },
        { name = "S3_INPUT_KEY", value = var.default_s3_input_key },
        { name = "WORK_DIR", value = "/app/work" },
        { name = "MODEL_NAME", value = "yolov8n-pose.pt" },
      ]
    }
  ])
}
