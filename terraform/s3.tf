resource "aws_s3_bucket" "input" {
  bucket = "${var.project_name}-input-${local.bucket_suffix_final}"
}

resource "aws_s3_bucket" "predict" {
  bucket = "${var.project_name}-predict-${local.bucket_suffix_final}"
}

resource "aws_s3_bucket" "output" {
  bucket = "${var.project_name}-output-${local.bucket_suffix_final}"
}

resource "aws_s3_bucket_public_access_block" "input" {
  bucket                  = aws_s3_bucket.input.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "predict" {
  bucket                  = aws_s3_bucket.predict.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "output" {
  bucket                  = aws_s3_bucket.output.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "input" {
  bucket = aws_s3_bucket.input.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "predict" {
  bucket = aws_s3_bucket.predict.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "output" {
  bucket = aws_s3_bucket.output.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "input" {
  bucket = aws_s3_bucket.input.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "predict" {
  bucket = aws_s3_bucket.predict.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "output" {
  bucket = aws_s3_bucket.output.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "transcribe_input" {
  bucket = "${var.transcribe_project_name}-input-${var.transcribe_input_bucket_suffix}"
}

resource "aws_s3_bucket" "transcribe_output" {
  bucket = "${var.transcribe_project_name}-output-${var.transcribe_output_bucket_suffix}"
}

resource "aws_s3_bucket_public_access_block" "transcribe_input" {
  bucket                  = aws_s3_bucket.transcribe_input.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "transcribe_output" {
  bucket                  = aws_s3_bucket.transcribe_output.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "transcribe_input" {
  bucket = aws_s3_bucket.transcribe_input.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "transcribe_output" {
  bucket = aws_s3_bucket.transcribe_output.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "transcribe_input" {
  bucket = aws_s3_bucket.transcribe_input.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "transcribe_output" {
  bucket = aws_s3_bucket.transcribe_output.id
  versioning_configuration {
    status = "Enabled"
  }
}
