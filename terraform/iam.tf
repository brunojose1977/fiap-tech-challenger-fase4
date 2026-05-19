data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name_prefix}-ecs-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name_prefix}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

data "aws_iam_policy_document" "task_s3" {
  statement {
    sid = "InputRead"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.input.arn,
      "${aws_s3_bucket.input.arn}/*",
    ]
  }

  statement {
    sid = "PredictWrite"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.predict.arn,
      "${aws_s3_bucket.predict.arn}/*",
    ]
  }

  statement {
    sid = "OutputWrite"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.output.arn,
      "${aws_s3_bucket.output.arn}/*",
    ]
  }

  statement {
    sid = "TranscribeInputRead"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.transcribe_input.arn,
      "${aws_s3_bucket.transcribe_input.arn}/*",
    ]
  }

  statement {
    sid = "TranscribeOutputWrite"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.transcribe_output.arn,
      "${aws_s3_bucket.transcribe_output.arn}/*",
    ]
  }
}

data "aws_iam_policy_document" "task_transcribe" {
  statement {
    sid = "TranscribeJobs"
    actions = [
      "transcribe:StartTranscriptionJob",
      "transcribe:GetTranscriptionJob",
      "transcribe:ListTranscriptionJobs",
      "transcribe:DeleteTranscriptionJob",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name   = "s3-pipeline"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.task_s3.json
}

resource "aws_iam_role_policy" "ecs_task_transcribe" {
  name   = "amazon-transcribe"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.task_transcribe.json
}
