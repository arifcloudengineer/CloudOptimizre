variable "function_name" {
  type    = string
  default = "cloudoptimizer-scanner"
}

variable "role_arn" { type = string }
variable "resources_table_name" { type = string }
variable "scan_history_table_name" { type = string }
variable "sns_topic_arn" { type = string }
variable "source_dir" {
  type        = string
  description = "Path to backend/ source code to package"
  default     = "../../../backend"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/build/cloudoptimizer_lambda.zip"
  excludes    = ["api", "tests", "__pycache__"]
}

resource "aws_lambda_function" "scanner" {
  function_name    = var.function_name
  role             = var.role_arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.12"
  timeout          = 300
  memory_size      = 512
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      RESOURCES_TABLE     = var.resources_table_name
      SCAN_HISTORY_TABLE  = var.scan_history_table_name
      SNS_TOPIC_ARN       = var.sns_topic_arn
      SAVINGS_ALERT_LIMIT = "50"
    }
  }
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.scanner.function_name}"
  retention_in_days = 14
}

output "function_arn" {
  value = aws_lambda_function.scanner.arn
}
output "function_name" {
  value = aws_lambda_function.scanner.function_name
}
