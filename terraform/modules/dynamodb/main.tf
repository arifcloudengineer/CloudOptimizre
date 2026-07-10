variable "table_name" {
  type    = string
  default = "cloudoptimizer-resources"
}

variable "tags" {
  type    = map(string)
  default = {}
}

resource "aws_dynamodb_table" "resources" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ResourceID"
  range_key    = "ScanDate"

  attribute {
    name = "ResourceID"
    type = "S"
  }
  attribute {
    name = "ScanDate"
    type = "S"
  }
  attribute {
    name = "ResourceType"
    type = "S"
  }

  global_secondary_index {
    name            = "ResourceType-index"
    hash_key        = "ResourceType"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, { Project = "CloudOptimizer" })
}

resource "aws_dynamodb_table" "scan_history" {
  name         = "${var.table_name}-scan-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ScanID"

  attribute {
    name = "ScanID"
    type = "S"
  }

  tags = merge(var.tags, { Project = "CloudOptimizer" })
}

output "table_name" {
  value = aws_dynamodb_table.resources.name
}
output "table_arn" {
  value = aws_dynamodb_table.resources.arn
}
output "scan_history_table_name" {
  value = aws_dynamodb_table.scan_history.name
}
output "scan_history_table_arn" {
  value = aws_dynamodb_table.scan_history.arn
}
