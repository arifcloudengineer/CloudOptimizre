terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    bucket         = "cloudoptimizer-tfstate"   # override in backend-config
    key            = "dev/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "cloudoptimizer-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

module "dynamodb" {
  source     = "../../modules/dynamodb"
  table_name = "cloudoptimizer-resources-${var.environment}"
  tags       = { Environment = var.environment }
}

module "sns" {
  source      = "../../modules/sns"
  topic_name  = "cloudoptimizer-alerts-${var.environment}"
  alert_email = var.alert_email
}

module "s3_reports" {
  source      = "../../modules/s3"
  bucket_name = "${var.reports_bucket_prefix}-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

module "iam" {
  source                  = "../../modules/iam"
  resources_table_arn     = module.dynamodb.table_arn
  scan_history_table_arn  = module.dynamodb.scan_history_table_arn
  sns_topic_arn           = module.sns.topic_arn
}

module "lambda" {
  source                   = "../../modules/lambda"
  function_name            = "cloudoptimizer-scanner-${var.environment}"
  role_arn                 = module.iam.lambda_role_arn
  resources_table_name     = module.dynamodb.table_name
  scan_history_table_name  = module.dynamodb.scan_history_table_name
  sns_topic_arn            = module.sns.topic_arn
}

module "eventbridge" {
  source                = "../../modules/eventbridge"
  lambda_function_arn   = module.lambda.function_arn
  lambda_function_name  = module.lambda.function_name
  schedule_expression   = var.scan_schedule
}

data "aws_caller_identity" "current" {}
