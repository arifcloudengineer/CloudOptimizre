variable "lambda_function_arn" { type = string }
variable "lambda_function_name" { type = string }

variable "schedule_expression" {
  type        = string
  description = "How often the scan runs"
  default     = "rate(1 day)"
}

resource "aws_cloudwatch_event_rule" "scheduled_scan" {
  name                = "cloudoptimizer-scheduled-scan"
  description         = "Triggers CloudOptimizer cost scan on a schedule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule      = aws_cloudwatch_event_rule.scheduled_scan.name
  target_id = "cloudoptimizer-scanner-lambda"
  arn       = var.lambda_function_arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_scan.arn
}

output "rule_arn" {
  value = aws_cloudwatch_event_rule.scheduled_scan.arn
}
