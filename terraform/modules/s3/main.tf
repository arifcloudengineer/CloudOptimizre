variable "bucket_name" { type = string }

resource "aws_s3_bucket" "reports" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket                  = aws_s3_bucket.reports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id
  rule {
    id     = "expire-old-reports"
    status = "Enabled"
    expiration {
      days = 90
    }
  }
}

output "bucket_name" {
  value = aws_s3_bucket.reports.bucket
}
output "bucket_arn" {
  value = aws_s3_bucket.reports.arn
}
