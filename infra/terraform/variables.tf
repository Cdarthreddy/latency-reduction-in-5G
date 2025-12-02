variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = "latency-orchestrator-data"
}

variable "ami_id" {
  description = "AMI ID for EC2 (Amazon Linux 2)"
  type        = string
  default     = "ami-0c02fb55956c7d316"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "key_name" {
  description = "SSH key name (optional - leave empty to not assign a key)"
  type        = string
  default     = ""
}

variable "git_repo_url" {
  description = "GitHub repo to clone"
  type        = string
  default     = "https://github.com/rishichowdary539/LatencyReductionInCloud.git"
}

variable "create_cloudwatch_log_group" {
  description = "Whether to create CloudWatch log group (set to false if it already exists)"
  type        = bool
  default     = true
}

variable "create_iam_resources" {
  description = "Whether to create IAM role and policies (requires IAM permissions). Set to false if running Terraform from EC2 without admin permissions."
  type        = bool
  default     = true
}