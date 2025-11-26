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
  name = "rl-orchestrator-role"

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

# -----------------------------
# 3. Attach S3 full access policy
# -----------------------------
resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
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
  key_name      = var.key_name

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
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
  name = "rl-orchestrator-profile"
  role = aws_iam_role.ec2_role.name
}
