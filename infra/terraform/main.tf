terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = var.aws_region
}

# -----------------------------
# 1. S3 bucket for artifacts
# -----------------------------
resource "aws_s3_bucket" "orchestrator_bucket" {
  bucket = var.bucket_name

  tags = {
    Name = "RL-Orchestrator-Data"
    Project = "LatencyReductionInCloud"
  }
}

# -----------------------------
# 2. IAM Role for EC2
# -----------------------------
resource "aws_iam_role" "ec2_role" {
  count = var.create_iam_resources ? 1 : 0
  name  = "LatencyOrchestratorRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Data source for existing IAM role (if not creating)
data "aws_iam_role" "existing_role" {
  count = var.create_iam_resources ? 0 : 1
  name  = "LatencyOrchestratorRole"
}

# -----------------------------
# 3. Attach S3 full access policy
# -----------------------------
resource "aws_iam_role_policy_attachment" "s3_attach" {
  count      = var.create_iam_resources ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# -----------------------------
# 3b. Attach CloudWatch Logs full access policy
# -----------------------------
resource "aws_iam_role_policy_attachment" "cloudwatch_logs_attach" {
  count      = var.create_iam_resources ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# -----------------------------
# 3c. Attach CloudWatch Metrics policy (for custom metrics)
# -----------------------------
resource "aws_iam_role_policy" "cloudwatch_metrics_policy" {
  count = var.create_iam_resources ? 1 : 0
  name  = "cloudwatch-metrics-policy"
  role  = aws_iam_role.ec2_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      }
    ]
  })
}

# -----------------------------
# 3d. CloudWatch Log Group for orchestrator logs
# -----------------------------
resource "aws_cloudwatch_log_group" "orchestrator_logs" {
  count             = var.create_cloudwatch_log_group ? 1 : 0
  name              = "/aws/latency-orchestrator/logs"
  retention_in_days = 7

  tags = {
    Name    = "LatencyOrchestratorLogs"
    Project = "LatencyReductionInCloud"
  }

  lifecycle {
    ignore_changes = [
      # Ignore if log group already exists (can be created manually)
    ]
  }
}

# Data source for existing CloudWatch log group (if not creating)
data "aws_cloudwatch_log_group" "existing_logs" {
  count = var.create_cloudwatch_log_group ? 0 : 1
  name  = "/aws/latency-orchestrator/logs"
}

# -----------------------------
# 4. Security group
# -----------------------------
resource "aws_security_group" "ec2_sg" {
  name        = "rl-training-sg"
  description = "Allow SSH and HTTP"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# -----------------------------
# 5. EC2 instance
# -----------------------------
resource "aws_instance" "rl_instance" {
  ami           = var.ami_id
  instance_type = var.instance_type
  # Only set key_name if provided (optional for some use cases)
  key_name      = var.key_name != "" ? var.key_name : null

  # Use created profile if creating IAM resources, otherwise use existing profile name
  # Note: When not creating IAM resources, we hardcode the name since we don't have permissions to read it
  iam_instance_profile = var.create_iam_resources ? aws_iam_instance_profile.ec2_profile[0].name : "LatencyOrchestratorRole"
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              cd /home/ec2-user
              sudo yum update -y
              sudo yum install -y python3 git
              git clone ${var.git_repo_url}
              cd tarun-project
              python3 -m venv venv
              source venv/bin/activate
              pip install -r requirements.txt
              python main_remote.py
              EOF

  tags = {
    Name = "RL-Training-Instance"
  }
}

# EC2 IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  count = var.create_iam_resources ? 1 : 0
  name  = "LatencyOrchestratorRole"  # Instance profile name usually matches role name
  role  = aws_iam_role.ec2_role[0].name
}

# Note: When create_iam_resources = false, we hardcode the instance profile name
# instead of using a data source because the EC2 instance doesn't have permission
# to read IAM instance profiles. We assume the instance profile exists and is
# named "LatencyOrchestratorRole" (same as the role name).
