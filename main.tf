# Providers
provider "aws" {
  region = "us-east-1"
}
provider "archive" {}

# Variables
variable "table_name" {
  default = "IPList"
}
variable "lambda_function_name" {
  default = "IPList_Shodan"
}
variable "shodan_key" {
  default = "8UIoSR8Cmi1ARGRUlLpNLXGiE8clARGQ"
}

# Creating DynamoDB Table
resource "aws_dynamodb_table" "IPtable" {
  name           = var.table_name
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "EIP"

  attribute {
    name = "EIP"
    type = "S"
  }

  tags = {
    Name = var.table_name
  }
}

# Archive lambda codes dir
data "archive_file" "zip" {
  type        = "zip"
  source_dir = "./lambda_codes"
  output_path = "hello_lambda.zip"
}

# Shodan encrypted key upload
resource "aws_ssm_parameter" "shodan_key" {
  name        = "shodan_key"
  type        = "SecureString"
  value       = var.shodan_key
}

# IAM Role for Lambda
resource "aws_iam_role" "IP_Lambda" {
  name = format("%s-role", var.lambda_function_name)

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  tags = {
    "Name" = format("%s-role", var.lambda_function_name)
  }
}

resource "aws_iam_policy" "lambda_logging" {
  name        = "lambda_logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeAddresses",
                "dms:DescribeReplicationInstances",
                "dynamodb:PutItem",
                "mq:ListBrokers",
                "ec2:DescribeRegions",
                "dynamodb:Scan",
                "dynamodb:UpdateItem",
                "ssm:GetParameters",
                "elasticloadbalancing:DescribeLoadBalancers",
                "es:ListDomainNames",
                "mq:DescribeBroker",
                "es:DescribeElasticsearchDomain",
                "rds:DescribeDBInstances",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.IP_Lambda.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

resource "aws_lambda_function" "example" {
    function_name = var.lambda_function_name
    role = aws_iam_role.IP_Lambda.arn
    runtime = "python3.8"
    handler = "lambda_function.lambda_handler"
    
    description = "Scrape the IPs and test them via Shodan API"
    timeout = 300
    filename = data.archive_file.zip.output_path
    environment {
      variables = {
        "dynamoDBTableName" = var.table_name
      }
    }

    tags = {
      "Name" = var.lambda_function_name
    }
}

