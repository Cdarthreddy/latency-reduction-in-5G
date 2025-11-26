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
  description = "SSH key name"
  type        = string
}

variable "git_repo_url" {
  description = "GitHub repo to clone"
  type        = string
  default     = "https://github.com/rishichowdary539/LatencyReductionInCloud.git"
}
