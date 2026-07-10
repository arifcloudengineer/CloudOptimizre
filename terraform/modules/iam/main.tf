variable "resources_table_arn" { type = string }
variable "scan_history_table_arn" { type = string }
variable "sns_topic_arn" { type = string }

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cloudoptimizer_lambda_role" {
  name               = "cloudoptimizer-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# Least-privilege read-only scan permissions.
# NOTE: deliberately NOT using AdministratorAccess or PowerUserAccess.
data "aws_iam_policy_document" "scan_permissions" {
  statement {
    sid    = "ReadOnlyResourceDiscovery"
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "elasticloadbalancing:Describe*",
      "rds:Describe*",
      "rds:ListTagsForResource",
      "s3:GetBucket*",
      "s3:ListBucket",
      "s3:ListAllMyBuckets",
      "s3:GetLifecycleConfiguration",
      "s3:GetBucketPolicyStatus",
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:GetMetricData",
      "tag:GetResources",
      "pricing:GetProducts",
      "ce:GetCostAndUsage"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "DynamoDBReadWrite"
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:UpdateItem",
      "dynamodb:BatchWriteItem"
    ]
    resources = [
      var.resources_table_arn,
      "${var.resources_table_arn}/index/*",
      var.scan_history_table_arn
    ]
  }

  statement {
    sid       = "PublishNotifications"
    effect    = "Allow"
    actions   = ["sns:Publish"]
    resources = [var.sns_topic_arn]
  }

  statement {
    sid    = "LambdaLogging"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_policy" "scan_permissions" {
  name   = "cloudoptimizer-scan-policy"
  policy = data.aws_iam_policy_document.scan_permissions.json
}

resource "aws_iam_role_policy_attachment" "attach" {
  role       = aws_iam_role.cloudoptimizer_lambda_role.name
  policy_arn = aws_iam_policy.scan_permissions.arn
}

# Separate, narrower policy for the "optimize" (remediation) Lambda.
# Only attach this to a role if automated remediation is explicitly enabled.
data "aws_iam_policy_document" "remediation_permissions" {
  statement {
    sid    = "SafeRemediationActions"
    effect = "Allow"
    actions = [
      "ec2:TerminateInstances",
      "ec2:DeleteVolume",
      "ec2:ReleaseAddress",
      "ec2:CreateSnapshot"
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/CloudOptimizerApproved"
      values   = ["true"]
    }
  }
}

resource "aws_iam_policy" "remediation_permissions" {
  name   = "cloudoptimizer-remediation-policy"
  policy = data.aws_iam_policy_document.remediation_permissions.json
}

output "lambda_role_arn" {
  value = aws_iam_role.cloudoptimizer_lambda_role.arn
}
output "lambda_role_name" {
  value = aws_iam_role.cloudoptimizer_lambda_role.name
}
output "remediation_policy_arn" {
  value = aws_iam_policy.remediation_permissions.arn
}
