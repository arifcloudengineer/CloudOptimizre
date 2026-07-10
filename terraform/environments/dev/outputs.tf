output "dashboard_table" {
  value = module.dynamodb.table_name
}

output "scanner_lambda_name" {
  value = module.lambda.function_name
}

output "alerts_topic_arn" {
  value = module.sns.topic_arn
}

output "reports_bucket" {
  value = module.s3_reports.bucket_name
}
