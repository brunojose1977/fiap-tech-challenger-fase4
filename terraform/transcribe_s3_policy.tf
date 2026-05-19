# Permite que o serviço Amazon Transcribe leia mídia de entrada e grave JSON bruto na saída.
data "aws_iam_policy_document" "transcribe_service_input" {
  statement {
    sid    = "AllowTranscribeReadInput"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["transcribe.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.transcribe_input.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "transcribe_input" {
  bucket = aws_s3_bucket.transcribe_input.id
  policy = data.aws_iam_policy_document.transcribe_service_input.json
}

data "aws_iam_policy_document" "transcribe_service_output" {
  statement {
    sid    = "AllowTranscribeWriteOutput"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["transcribe.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.transcribe_output.arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "transcribe_output" {
  bucket = aws_s3_bucket.transcribe_output.id
  policy = data.aws_iam_policy_document.transcribe_service_output.json
}
