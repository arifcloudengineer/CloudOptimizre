variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "alert_email" {
  type    = string
  default = ""
}

variable "reports_bucket_prefix" {
  type    = string
  default = "cloudoptimizer-reports"
}

variable "scan_schedule" {
  type    = string
  default = "rate(1 day)"
}
