variable "topic_name" {
  type    = string
  default = "cloudoptimizer-alerts"
}

variable "alert_email" {
  type        = string
  description = "Email address to receive cost/security alerts"
  default     = ""
}

resource "aws_sns_topic" "alerts" {
  name = var.topic_name
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

output "topic_arn" {
  value = aws_sns_topic.alerts.arn
}
